import json

def load(file):
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: {file} doesn't exists")

def dump(data,file):
    with open(file,'w') as f:
        json.dump(data,f,indent=2)