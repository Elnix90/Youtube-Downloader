from typing import Any


def compare_dicts(
    dict1: dict[str, Any],
    dict2: dict[str, Any],  # pyright: ignore[reportExplicitAny]
) -> None:
    """
    Compare two dictionaries and print the differences.
    Shows keys missing, extra, or with different values.
    """
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())

    # Keys present in dict1 but not in dict2
    for key in keys1 - keys2:
        print(f"Only in dict1: {key} = {dict1[key]}")

    # Keys present in dict2 but not in dict1
    for key in keys2 - keys1:
        print(f"Only in dict2: {key} = {dict2[key]}")

    # Keys present in both, but with different values
    for key in keys1 & keys2:
        if dict1[key] != dict2[key]:
            print(
                f"Different value for key '{key}': dict1 = {dict1[key]} | dict2 = {dict2[key]}"
            )
