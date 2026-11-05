def get_roadmap_steps(result: dict) -> list:
    """Return roadmap steps in their generated order."""
    steps = result.get("roadmap", [])
    if not isinstance(steps, list):
        return []
    return sorted(
        steps,
        key=lambda item: item.get("step", 999)
        if isinstance(item, dict) else 999
    )
