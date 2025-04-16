import json

with open("output.json", "r") as f:
    data = json.load(f)
print(len(data))
