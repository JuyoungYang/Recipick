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
    """사용자가 입력한 재료, 선호 음식, 조리 방식 처리"""
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
    """AI 추천 레시피 목록 조회"""
    try:
        recipes = Recipe.objects.all()[:5]
        serializer = RecipeListSerializer(recipes, many=True)

        return Response({"status": settings.STATUS_SUCCESS, "recipes": serializer.data})
    except Exception as e:
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": "레시피 추천 중 오류가 발생했습니다.",
            },
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
        return Response(
            {"status": settings.STATUS_SUCCESS, "filtered_recipes": serializer.data}
        )

    except ValueError:
        return Response(
            {"status": settings.STATUS_ERROR, "message": "잘못된 입력값입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["GET"])
def recipe_detail(request, recipe_id):
    """특정 레시피 상세 정보 조회"""
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
            {"status": settings.STATUS_ERROR, "message": settings.UNKNOWN_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def refresh_recommendations(request):
    """새로운 추천 레시피 요청 처리"""
    serializer = RefreshRecommendationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": "잘못된 입력입니다.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user_id = serializer.validated_data["user_id"]
        recipes = Recipe.objects.all()[:5]

        return Response(
            {
                "status": settings.STATUS_SUCCESS,
                "message": "새로운 추천 리스트가 생성되었습니다.",
                "recipes": RecipeListSerializer(recipes, many=True).data,
            }
        )
    except Exception as e:
        return Response(
            {
                "status": settings.STATUS_ERROR,
                "message": "추천 새로고침 중 오류가 발생했습니다.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class GenerateInstructionsView(APIView):
    def get(self, request, recipe_id):
        try:
            recipe = get_object_or_404(Recipe, id=recipe_id)

            # 1. 데이터베이스에서 조리 방법 확인
            if recipe.CKG_METHOD_CN:
                return Response(
                    {
                        "status": settings.STATUS_SUCCESS,
                        "recipe_name": recipe.CKG_NM,
                        "instructions": recipe.CKG_METHOD_CN,
                        "source": "database",
                    }
                )

            # 2. 데이터베이스에 없는 경우 GPT로 생성
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            prompt = f"""
            레시피 이름: {recipe.CKG_NM}
            필요한 재료: {recipe.CKG_MTRL_CN}
            조리 시간: {recipe.CKG_TIME_NM}
            인분: {recipe.CKG_INBUN_NM}
            
            위 레시피의 상세한 조리 방법을 단계별로 설명해주세요.
            """

            response = client.chat.completions.create(
                model=settings.GPT_MODEL_NAME,
                messages=[
                    {"role": "system", "content": settings.SYSTEM_RECIPE_EXPERT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            instructions = response.choices[0].message.content

            # 생성된 레시피를 데이터베이스에 저장
            recipe.CKG_METHOD_CN = instructions
            recipe.save()

            return Response(
                {
                    "status": settings.STATUS_SUCCESS,
                    "recipe_name": recipe.CKG_NM,
                    "instructions": instructions,
                    "source": "ai",
                }
            )

        except Recipe.DoesNotExist:
            return Response(
                {
                    "status": settings.STATUS_ERROR,
                    "message": "레시피를 찾을 수 없습니다.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"status": settings.STATUS_ERROR, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
