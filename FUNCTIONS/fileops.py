import json
from pathlib import Path

def load(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: {file} doesn't exists")

def dump(data,file):
    with open(file,'w') as f:
        json.dump(data,f,indent=2)

def load_patterns(file_path):
    if not Path(file_path).exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        patterns = set()
        for line in f:
            if line.strip() and ("#" not in line):
                patterns.add(line.strip())
        return patterns
