from django.db import models

class Recipe(models.Model):
    recipe_name = models.CharField(max_length=255, unique=True)  # null=True 제거
    cook_time = models.CharField(max_length=50)  # 조리 시간
    servings = models.CharField(max_length=50)  # 인분 수
    ingredients = models.TextField()  # 재료 (JSON 저장 가능)
    instructions = models.TextField()  # 조리 순서 (JSON 저장 가능)
    image_url = models.CharField(max_length=500, blank=True, null=True)  # 이미지 URL

    def __str__(self):
        return self.recipe_name

# JSON 저장이 필요한 경우 ingredients와 instructions 필드는 JSONField로 변경 가능

