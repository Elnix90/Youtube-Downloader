import os
from pathlib import Path
import subprocess
import ast






def is_git_ignored(path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False





def get_file_docstring(path: Path) -> str | None:
    if path.suffix != ".py":
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read())
            doc = ast.get_docstring(node)
            if doc:
                first_line = doc.strip().splitlines()[0]
                return first_line
    except Exception:
        return None
    return None





def print_tree(root_dir: Path, prefix: str = ""):
    entries = sorted(os.listdir(root_dir))
    for i, item in enumerate(entries):
        path = root_dir / item

        if is_git_ignored(path):
            continue  # skip ignored files

        connector = "├── " if i < len(entries) - 1 else "└── "
        line = prefix + connector + item

        doc_line = get_file_docstring(path)
        if doc_line:
            line += f"  # {doc_line}"

        print(line)

        if path.is_dir():
            print_tree(path, prefix + ("│   " if i < len(entries) - 1 else "    "))

# Run from current directory
print_tree(Path("."))
