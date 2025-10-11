"""
Computes and prints a tree view of the project?
Ignores .gitignore files and adds docstrings
"""

import ast
import subprocess
from pathlib import Path


def is_git_ignored(path: Path) -> bool:
    """
    Returns a bool if the file is in one of the .gitignore
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_file_docstring(path: Path) -> str | None:
    """
    Fetch the docstring of a file given in args
    """
    if path.suffix != ".py":
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read())
            doc = ast.get_docstring(node)
            if doc:
                first_line = doc.strip().splitlines()[0]
                return first_line
    except Exception:  # pylint: disable=broad-exception-caught
        return None
    return None


def print_tree(root_dir: Path, prefix: str = ""):
    """
    Show the tree view
    """
    entries = sorted(root_dir.iterdir())
    for i, path in enumerate(entries):

        if is_git_ignored(path):
            continue  # skip ignored files

        connector = "├── " if i < len(entries) - 1 else "└── "
        line = prefix + connector + path.name

        doc_line = get_file_docstring(path)
        if doc_line:
            line += f"  # {doc_line}"

        print(line)

        if path.is_dir():
            print_tree(path, prefix + ("│   " if i < len(entries) - 1 else "    "))


# Run from current directory
print_tree(Path("."))
