from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import openai
from .models import Recipe
from .serializers import (
    RecipeInputSerializer,
    RecipeListSerializer,
    FilteredRecipeSerializer,
    RecipeDetailSerializer,
    RefreshRecommendationSerializer,
)


@api_view(["POST"])
def input_ingredients(request):
    serializer = RecipeInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": "잘못된 입력입니다.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {"status": settings.STATUS_SUCCESS, "message": "입력된 재료가 저장되었습니다."}
    )


@api_view(["GET"])
def recommend_recipes(request):
    try:
        recipes = Recipe.objects.all()[:5]
        serializer = RecipeListSerializer(recipes, many=True)

        return Response({"status": settings.STATUS_SUCCESS, "recipes": serializer.data})
    except Exception:
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": "레시피 추천 중 오류가 발생했습니다.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def recipe_detail(request, recipe_id):
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer = RecipeDetailSerializer(recipe)
        return Response({"status": settings.STATUS_SUCCESS, "recipe": serializer.data})
    except Recipe.DoesNotExist:
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": "해당 레시피를 찾을 수 없습니다.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        return Response(
            {"status": settings.STATUS_ERROR, "message": settings.UNKNOWN_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
