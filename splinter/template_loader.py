import yaml

def load_template(path):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data
