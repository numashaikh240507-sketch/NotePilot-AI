def get_action_items(result: dict) -> list:
    """Return validated action items from the NotePilot result."""
    items = result.get("action_items", [])
    return items if isinstance(items, list) else []
