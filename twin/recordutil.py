"""Small record-field helpers shared by the seed and the write routes."""


def clean_fields(fields: dict) -> dict:
    """Drop empty cells (None / "" / False / []) the way Airtable omits them."""
    return {
        k: v
        for k, v in fields.items()
        if v is not None and v is not False and v != "" and v != []
    }
