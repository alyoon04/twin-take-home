"""In-memory twin state.

S3: ported as-is from the starter (a plain dict + in-place reset).
S5 replaces this with the deterministic store (seed graph, fixed clock,
per-type ID counters) described in docs/ARCHITECTURE.md.
"""

from copy import deepcopy

DEFAULT_STATE = {
    "provider": "airtable",
    "example_resources": [
        {"id": "res_twin_001", "object": "example_resource", "name": "Seed resource"}
    ],
}

# Mutated in place by reset_state() so module-level references stay valid.
state = deepcopy(DEFAULT_STATE)


def reset_state() -> None:
    """Reset state to the deterministic default."""
    state.clear()
    state.update(deepcopy(DEFAULT_STATE))
