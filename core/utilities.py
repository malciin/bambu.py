from typing import TypeVar

T = TypeVar("T")

def get_or_none(dict: dict[str, T], key: str) -> T:
    if key not in dict: return None

    return dict[key]
