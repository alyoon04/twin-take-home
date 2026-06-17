#!/usr/bin/env python3
"""Black-box verification for the Airtable Web API twin.

Runs against a running instance (default http://localhost:8080; override with
TWIN_BASE_URL). Mirrors Arga's loop: wait for health, reset deterministic state,
then send provider-shaped requests and check the responses. Exits non-zero on any
failure. Zero dependencies (stdlib only).

    uv run python scripts/verify.py
    TWIN_BASE_URL=http://localhost:8080 python3 scripts/verify.py
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("TWIN_BASE_URL", "http://localhost:8080").rstrip("/")
VALID = "Bearer twin-fake-pat_developer_full-scope_DO-NOT-USE"
INVALID = "Bearer twin-fake-pat_invalid_example_DO-NOT-USE"
AUTH = {"Authorization": VALID}
CRM = "app1MrVfxTUgJuBm0"  # deterministic seed base id

_results: list[tuple[str, bool]] = []


def request(method, path, headers=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read() or "null")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw or "null")
        except json.JSONDecodeError:
            return e.code, None


def wait_for_health(timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if request("GET", "/_arga/healthz")[0] == 200:
                return True
        except Exception:
            pass  # connection refused / reset while uvicorn boots
        time.sleep(0.5)
    return False


def check(name, ok):
    _results.append((name, bool(ok)))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")


def main():
    print(f"Verifying twin at {BASE}\n")
    if not wait_for_health():
        print("Health check never passed; is the container running?")
        sys.exit(1)

    s, b = request("GET", "/_arga/healthz")
    check("health -> 200 {status: ok}", s == 200 and b == {"status": "ok"})

    check("reset -> 200", request("POST", "/_arga/admin/reset")[0] == 200)

    s, b = request("GET", "/_arga/admin/state")
    check("state snapshot has 2 bases", s == 200 and b["counts"]["bases"] == 2)

    check("missing auth -> 401", request("GET", f"/v0/{CRM}/Contacts")[0] == 401)
    s, b = request("GET", f"/v0/{CRM}/Contacts", {"Authorization": INVALID})
    check("invalid auth -> 401 AUTHENTICATION_REQUIRED", s == 401 and b["error"]["type"] == "AUTHENTICATION_REQUIRED")

    s, b = request("GET", f"/v0/{CRM}/Contacts", AUTH)
    check("list seeded records (5)", s == 200 and len(b["records"]) == 5)

    s, b = request("POST", f"/v0/{CRM}/Contacts", AUTH, {"fields": {"Name": "Verify Bot"}})
    check("create -> rec id + createdTime", s == 200 and b["id"].startswith("rec") and "createdTime" in b)
    rid = b.get("id")

    s, b = request("PATCH", f"/v0/{CRM}/Contacts/{rid}", AUTH, {"fields": {"Company": "Arga"}})
    check("patch merges (keeps Name)", s == 200 and b["fields"].get("Company") == "Arga" and b["fields"].get("Name") == "Verify Bot")

    s, b = request("DELETE", f"/v0/{CRM}/Contacts/{rid}", AUTH)
    check("delete -> {deleted: true}", s == 200 and b == {"deleted": True, "id": rid})

    s, b = request("GET", f"/v0/{CRM}/Contacts?pageSize=2", AUTH)
    check("pagination returns offset", s == 200 and len(b["records"]) == 2 and "offset" in b)

    q = urllib.parse.quote("{Company}='NASA'")
    s, b = request("GET", f"/v0/{CRM}/Contacts?filterByFormula={q}", AUTH)
    check("filterByFormula filters to 1", s == 200 and len(b["records"]) == 1)

    s, b = request("GET", f"/v0/{CRM}/Contacts/recDoesNotExist0", AUTH)
    check("record 404 -> bare {error: NOT_FOUND}", s == 404 and b == {"error": "NOT_FOUND"})

    s, b = request("GET", "/v0/meta/whoami", AUTH)
    check("meta whoami -> usr id", s == 200 and b["id"].startswith("usr"))

    s, b = request("GET", "/v0/meta/bases", AUTH)
    check("meta list bases (2)", s == 200 and len(b["bases"]) == 2)

    wid = request("GET", f"/v0/bases/{CRM}/webhooks", AUTH)[1]["webhooks"][0]["id"]
    request("POST", f"/v0/{CRM}/Contacts", AUTH, {"fields": {"Name": "Event Maker"}})
    s, b = request("GET", f"/v0/bases/{CRM}/webhooks/{wid}/payloads", AUTH)
    check("record mutation generates a webhook payload", s == 200 and len(b["payloads"]) >= 1)

    request("POST", "/_arga/admin/rate-limit", body={"enabled": True, "perBase": 3})
    statuses = [request("GET", f"/v0/{CRM}/Contacts", AUTH)[0] for _ in range(4)]
    check("rate limit -> 429 after threshold", statuses[-1] == 429)
    request("POST", "/_arga/admin/reset")

    passed = sum(1 for _, ok in _results if ok)
    print(f"\n{passed}/{len(_results)} checks passed")
    sys.exit(0 if passed == len(_results) else 1)


if __name__ == "__main__":
    main()
