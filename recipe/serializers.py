from rest_framework import serializers
from .models import Recipe


class RecipeInputSerializer(serializers.Serializer):
    """사용자 입력 처리 (/api/recipes/input/)"""

    ingredients = serializers.ListField(child=serializers.CharField())
    preferences = serializers.CharField()
    cooking_method = serializers.CharField()


class RecipeListSerializer(serializers.ModelSerializer):
    """추천 레시피 목록 조회 (/api/recipes/recommend/)"""

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cook_time", "servings"]


class FilteredRecipeSerializer(serializers.ModelSerializer):
    """필터링된 레시피 목록 조회 (/api/recipes/filter/)"""

    class Meta:
        model = Recipe
        fields = ["id", "name", "cook_time", "servings"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    """레시피 상세 정보 조회 (/api/recipes/{recipe_id}/)"""

    class Meta:
        model = Recipe
        fields = [
            "id",
            "name",
            "image",
            "cook_time",
            "servings",
            "ingredients",
            "instructions",
        ]


class RefreshRecommendationSerializer(serializers.Serializer):
    """추천 레시피 새로고침 (/api/recipes/recommend/refresh/)"""

    user_id = serializers.IntegerField()
