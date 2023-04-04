
def to_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    return None
