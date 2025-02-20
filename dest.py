import chardet

with open("data/recipe_01.csv", "rb") as f:
    result = chardet.detect(f.read())

print(f"Detected encoding: {result['encoding']}")
