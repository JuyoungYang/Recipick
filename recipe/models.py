from django.db import models
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import openai
from .serializers import (
    RecipeInputSerializer,
    RecipeListSerializer,
    FilteredRecipeSerializer,
    RecipeDetailSerializer,
    RefreshRecommendationSerializer,
)

class Recipe(models.Model):
    CKG_NM = models.CharField(
        max_length=255,
        verbose_name="요리명",
        null=True,
    )
    CKG_MTRL_CN = models.TextField(
        verbose_name="재료 목록",
        null=True,
    )
    CKG_INBUN_NM = models.CharField(
        max_length=50,
        verbose_name="인분 수",
        null=True,
    )
    CKG_TIME_NM = models.CharField(
        max_length=50,
        verbose_name="조리 시간",
        null=True,
    )
    RCP_IMG_URL = models.TextField(
        verbose_name="레시피 이미지",
        null=True,
    )
    CKG_METHOD_CN = models.TextField(
        verbose_name="조리 방법",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 날짜")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정 날짜")

    class Meta:
        db_table = "recipes"
        verbose_name = "레시피"
        verbose_name_plural = "레시피"

    def __str__(self):
        return self.CKG_NM if self.CKG_NM else "레시피 이름 없음"

    @property
    def image(self):
        return self.RCP_IMG_URL

    @property
    def cook_time(self):
        return self.CKG_TIME_NM

    @property
    def servings(self):
        return self.CKG_INBUN_NM

    @property
    def ingredients(self):
        return self.CKG_MTRL_CN

    @property
    def instructions(self):
        return self.CKG_METHOD_CN

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
    Recipe.objects.create(
        CKG_NM=serializer.validated_data.get("ingredients"),
        CKG_MTRL_CN=serializer.validated_data.get("preferences"),
        CKG_METHOD_CN=serializer.validated_data.get("cooking_method"),
    )
    return Response(
        {"status": settings.STATUS_SUCCESS, "message": "입력된 재료가 저장되었습니다."}
    )

@api_view(["GET"])
def recommend_recipes(request):
    try:
        recipes = Recipe.objects.all().order_by("-created_at")[:5]
        serializer = RecipeListSerializer(recipes, many=True)
        return Response({"status": settings.STATUS_SUCCESS, "recipes": serializer.data})
    except Exception as e:
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": f"레시피 추천 중 오류가 발생했습니다: {str(e)}",
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
    except Exception as e:
        return Response(
            {"status": settings.STATUS_ERROR, "message": f"오류 발생: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
