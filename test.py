import json

with open("output.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print(len(data))
