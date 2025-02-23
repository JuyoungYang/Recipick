"""
레시피 API 뷰
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Recipe
from .serializers import (
    RecipeInputSerializer,
    RecipeListSerializer,  # recommend_recipes에서 사용
    FilteredRecipeSerializer,  # filter_recipes에서 사용
    RecipeDetailSerializer,  # recipe_detail에서 사용
    RefreshRecommendationSerializer,  # refresh_recommendations에서 사용
)


@api_view(["POST"])
def input_ingredients(request):
    """사용자가 입력한 재료, 선호 음식, 조리 방식 처리"""
    serializer = RecipeInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "message": "잘못된 입력입니다.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # TODO: 실제 재료 저장 로직 구현

    return Response({"status": "success", "message": "입력된 재료가 저장되었습니다."})


@api_view(["GET"])
def recommend_recipes(request):
    """AI 추천 레시피 목록 조회"""
    try:
        # TODO: 실제 AI 추천 로직 구현
        recipes = Recipe.objects.all()[:5]
        serializer = RecipeListSerializer(recipes, many=True)

        return Response({"status": "success", "recipes": serializer.data})
    except Exception as e:
        return Response(
            {"status": "error", "message": "레시피 추천 중 오류가 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def filter_recipes(request):
    """조리시간, 인분 기준 레시피 필터링"""
    try:
        cook_time = request.query_params.get("cook_time")
        servings = request.query_params.get("servings")

        recipes = Recipe.objects.all()

        if cook_time:
            min_time, max_time = map(int, cook_time.split("-"))
            recipes = recipes.filter(cook_time__gte=min_time, cook_time__lte=max_time)

        if servings:
            recipes = recipes.filter(servings=int(servings))

        serializer = FilteredRecipeSerializer(recipes, many=True)
        return Response({"status": "success", "filtered_recipes": serializer.data})

    except ValueError:
        return Response(
            {"status": "error", "message": "잘못된 입력값입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
def recipe_detail(request, recipe_id):
    """특정 레시피 상세 정보 조회"""
    try:
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer = RecipeDetailSerializer(recipe)
        return Response({"status": "success", "recipe": serializer.data})
    except Recipe.DoesNotExist:
        return Response(
            {"status": "error", "message": "해당 레시피를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": "레시피 조회 중 오류가 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def refresh_recommendations(request):
    """새로운 추천 레시피 요청 처리"""
    serializer = RefreshRecommendationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "status": "error",
                "message": "잘못된 입력입니다.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user_id = serializer.validated_data["user_id"]
        # TODO: 실제 새로운 추천 로직 구현
        recipes = Recipe.objects.all()[:5]

        return Response(
            {
                "status": "success",
                "message": "새로운 추천 리스트가 생성되었습니다.",
                "recipes": RecipeListSerializer(recipes, many=True).data,
            }
        )
    except Exception as e:
        return Response(
            {"status": "error", "message": "추천 새로고침 중 오류가 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
