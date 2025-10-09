"""
find_duplicates.py
"""


def find_duplicates(items: list[str]) -> list[str]:
    """
    Return all duplicate items from a list, preserving order.
    Each duplicate will appear only once in the output.
    """
    seen = set[str]()
    duplicates: list[str] = []
    for item in items:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return duplicates
