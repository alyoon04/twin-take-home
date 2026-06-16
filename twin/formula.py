"""A faithful subset of the Airtable formula language for ``filterByFormula``
(AIRTABLE_SPEC.md section 7).

Pipeline: ``compile_formula(text, field_names, id_to_name)`` tokenizes + parses
(raising ``FormulaError`` on malformed syntax or an unknown field name -> the
router turns that into ``422 INVALID_FILTER_BY_FORMULA``). ``matches(node, fields)``
evaluates the AST against one record's fields and returns whether it is included:
a record is kept unless the result is one of ``0 / false / "" / NaN / [] / #Error!``.

Supported: ``{Field}`` / bare field refs (by name or id), string/number literals,
``TRUE()/FALSE()/BLANK()``, comparison (``= != < > <= >=``), arithmetic
(``+ - * /``), ``&`` concat, and the functions in ``_FUNCTIONS``. Out of scope
(documented gap): date/time, regex, array/rollup, and record-meta functions.
"""

import re

KNOWN_FUNCTIONS = {
    "AND", "OR", "NOT", "XOR", "IF", "SWITCH", "TRUE", "FALSE", "BLANK",
    "CONCATENATE", "FIND", "SEARCH", "LOWER", "UPPER", "LEN", "TRIM",
    "LEFT", "RIGHT", "MID", "ABS", "ROUND", "MOD", "MAX", "MIN", "VALUE",
}
_LAZY = {"AND", "OR", "NOT", "XOR", "IF", "SWITCH"}


class FormulaError(Exception):
    """Malformed formula or unknown field -> 422 INVALID_FILTER_BY_FORMULA."""


class _EvalError(Exception):
    """Per-record runtime error (#Error!) -> the record is excluded."""


# --- tokenizer ------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
      (?P<WS>\s+)
    | (?P<NUMBER>\d+\.\d+|\.\d+|\d+)
    | (?P<STRING>'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")
    | (?P<FIELD>\{(?:[^}\\]|\\.)*\})
    | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<OP><=|>=|!=|=|<|>|\+|-|\*|/|&)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<COMMA>,)
    """,
    re.VERBOSE,
)


def _unescape(s: str) -> str:
    return re.sub(r"\\(.)", r"\1", s)


def _tokenize(text: str) -> list:
    tokens = []
    pos = 0
    for m in _TOKEN_RE.finditer(text):
        if m.start() != pos:
            raise FormulaError("unexpected character")
        pos = m.end()
        kind = m.lastgroup
        if kind == "WS":
            continue
        value = m.group()
        if kind in ("STRING", "FIELD"):
            value = _unescape(value[1:-1])
        tokens.append((kind, value))
    if pos != len(text):
        raise FormulaError("unexpected character")
    return tokens


# --- parser ---------------------------------------------------------------

class _Parser:
    def __init__(self, tokens: list, field_names: set, id_to_name: dict) -> None:
        self.t = tokens
        self.i = 0
        self.field_names = field_names
        self.id_to_name = id_to_name

    def _peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def _advance(self):
        tok = self._peek()
        self.i += 1
        return tok

    def _resolve_field(self, ref: str) -> str:
        if ref in self.field_names:
            return ref
        if ref in self.id_to_name:
            return self.id_to_name[ref]
        raise FormulaError(f"Unknown field names: {ref}")

    def parse(self):
        if not self.t:
            raise FormulaError("empty formula")
        node = self._comparison()
        if self.i != len(self.t):
            raise FormulaError("trailing tokens")
        return node

    def _comparison(self):
        left = self._additive()
        kind, val = self._peek()
        if kind == "OP" and val in ("=", "!=", "<", ">", "<=", ">="):
            self._advance()
            return ("cmp", val, left, self._additive())
        return left

    def _additive(self):
        node = self._multiplicative()
        while True:
            kind, val = self._peek()
            if kind == "OP" and val in ("+", "-", "&"):
                self._advance()
                node = ("bin", val, node, self._multiplicative())
            else:
                return node

    def _multiplicative(self):
        node = self._unary()
        while True:
            kind, val = self._peek()
            if kind == "OP" and val in ("*", "/"):
                self._advance()
                node = ("bin", val, node, self._unary())
            else:
                return node

    def _unary(self):
        kind, val = self._peek()
        if kind == "OP" and val == "-":
            self._advance()
            return ("neg", self._unary())
        return self._primary()

    def _primary(self):
        kind, val = self._peek()
        if kind == "NUMBER":
            self._advance()
            return ("num", float(val) if "." in val else int(val))
        if kind == "STRING":
            self._advance()
            return ("str", val)
        if kind == "FIELD":
            self._advance()
            return ("field", self._resolve_field(val))
        if kind == "LPAREN":
            self._advance()
            node = self._comparison()
            self._expect("RPAREN")
            return node
        if kind == "IDENT":
            self._advance()
            if self._peek()[0] == "LPAREN":
                name = val.upper()
                if name not in KNOWN_FUNCTIONS:
                    raise FormulaError(f"unknown function {val}")
                self._advance()
                args = []
                if self._peek()[0] != "RPAREN":
                    args.append(self._comparison())
                    while self._peek()[0] == "COMMA":
                        self._advance()
                        args.append(self._comparison())
                self._expect("RPAREN")
                return ("call", name, args)
            return ("field", self._resolve_field(val))  # bare single-word field
        raise FormulaError("unexpected token")

    def _expect(self, kind: str):
        if self._peek()[0] != kind:
            raise FormulaError(f"expected {kind}")
        return self._advance()


def compile_formula(text: str, field_names: set, id_to_name: dict):
    return _Parser(_tokenize(text), field_names, id_to_name).parse()


# --- evaluation -----------------------------------------------------------

def matches(node, fields: dict) -> bool:
    try:
        value = _eval(node, fields)
    except _EvalError:
        return False
    return _truthy(value)


def _truthy(v) -> bool:
    if v is None or v is False:
        return False
    if isinstance(v, float) and v != v:  # NaN
        return False
    if v == 0 or v == "" or v == []:
        return False
    return True


def _eval(node, fields):
    kind = node[0]
    if kind == "num" or kind == "str":
        return node[1]
    if kind == "field":
        return fields.get(node[1])
    if kind == "neg":
        return -_num(_eval(node[1], fields))
    if kind == "cmp":
        return _compare(node[1], _eval(node[2], fields), _eval(node[3], fields))
    if kind == "bin":
        return _binop(node[1], _eval(node[2], fields), _eval(node[3], fields))
    if kind == "call":
        name, arg_nodes = node[1], node[2]
        if name in _LAZY:
            return _eval_lazy(name, arg_nodes, fields)
        return _call(name, [_eval(a, fields) for a in arg_nodes])
    raise _EvalError("bad node")


def _eval_lazy(name, args, fields):
    if name == "AND":
        return all(_truthy(_eval(a, fields)) for a in args)
    if name == "OR":
        return any(_truthy(_eval(a, fields)) for a in args)
    if name == "NOT":
        return not _truthy(_eval(args[0], fields))
    if name == "XOR":
        return sum(1 for a in args if _truthy(_eval(a, fields))) % 2 == 1
    if name == "IF":
        if _truthy(_eval(args[0], fields)):
            return _eval(args[1], fields)
        return _eval(args[2], fields) if len(args) > 2 else 0
    if name == "SWITCH":
        subject = _eval(args[0], fields)
        rest = args[1:]
        i = 0
        while i + 1 < len(rest):
            if _equal(subject, _eval(rest[i], fields)):
                return _eval(rest[i + 1], fields)
            i += 2
        return _eval(rest[-1], fields) if len(rest) % 2 == 1 else None
    raise _EvalError("bad lazy")


def _call(name, args):
    if name == "TRUE":
        return 1
    if name == "FALSE":
        return 0
    if name == "BLANK":
        return None
    if name == "LOWER":
        return _str(args[0]).lower()
    if name == "UPPER":
        return _str(args[0]).upper()
    if name == "TRIM":
        return _str(args[0]).strip()
    if name == "LEN":
        return len(_str(args[0]))
    if name == "CONCATENATE":
        return "".join(_str(a) for a in args)
    if name == "FIND":
        start = int(_num(args[2])) - 1 if len(args) > 2 else 0
        pos = _str(args[1]).find(_str(args[0]), max(0, start))
        return pos + 1 if pos >= 0 else 0
    if name == "SEARCH":
        start = int(_num(args[2])) - 1 if len(args) > 2 else 0
        pos = _str(args[1]).lower().find(_str(args[0]).lower(), max(0, start))
        return pos + 1 if pos >= 0 else None
    if name == "LEFT":
        n = int(_num(args[1])) if len(args) > 1 else 1
        return _str(args[0])[:max(0, n)]
    if name == "RIGHT":
        n = int(_num(args[1])) if len(args) > 1 else 1
        return _str(args[0])[-n:] if n > 0 else ""
    if name == "MID":
        start = max(0, int(_num(args[1])) - 1)
        return _str(args[0])[start:start + int(_num(args[2]))]
    if name == "ABS":
        return abs(_num(args[0]))
    if name == "ROUND":
        return round(_num(args[0]), int(_num(args[1])) if len(args) > 1 else 0)
    if name == "MOD":
        divisor = _num(args[1])
        if divisor == 0:
            raise _EvalError("mod by zero")
        return _num(args[0]) % divisor
    if name == "MAX":
        return max(_num(a) for a in args)
    if name == "MIN":
        return min(_num(a) for a in args)
    if name == "VALUE":
        return _num(args[0])
    raise _EvalError(f"unhandled {name}")


# --- coercion helpers -----------------------------------------------------

def _num(v):
    if v is None:
        return 0
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = v.strip()
        try:
            return float(s) if ("." in s or "e" in s.lower()) else int(s)
        except ValueError:
            raise _EvalError("not a number")
    raise _EvalError("not a number")


def _str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, list):
        return ",".join(_str(x) for x in v)
    return str(v)


def _coerce(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return 1 if v else 0
    return v


def _equal(a, b) -> bool:
    a, b = _coerce(a), _coerce(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    return _str(a) == _str(b)


def _order(v):
    v = _coerce(v)
    if isinstance(v, (int, float)):
        return (0, v)
    return (1, _str(v))


def _compare(op, a, b) -> bool:
    if op == "=":
        return _equal(a, b)
    if op == "!=":
        return not _equal(a, b)
    x, y = _order(a), _order(b)
    if op == "<":
        return x < y
    if op == ">":
        return x > y
    if op == "<=":
        return x <= y
    return x >= y


def _binop(op, a, b):
    if op == "&":
        return _str(a) + _str(b)
    x, y = _num(a), _num(b)
    if op == "+":
        return x + y
    if op == "-":
        return x - y
    if op == "*":
        return x * y
    if y == 0:  # op == "/"
        return float("nan") if x == 0 else float("inf")
    return x / y
