# recipe/utils.py
import csv
from .models import Recipe
def load_recipes_from_csv(file_path):
    # euc-kr 인코딩으로 열기
    with open(file_path, newline='', encoding='cp949') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            image_url = row.get("image", "").strip()
            if not image_url:
                image_url = "/static/images/default.png"
            Recipe.objects.create(
                name=row.get("name", ""),
                image=image_url,
                cook_time=row.get("cook_time", ""),
                servings=int(row.get("servings", 0)),
                ingredients=row.get("ingredients", ""),
                instructions=row.get("instructions", "")
            )
