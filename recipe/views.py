import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status   

from .models import Recipe
from .serializers import RecipeSerializer
from chatbot.models import ChatLog

# 1) 재료 입력 - /api/recipes/input/ (POST)
class RecipeInputView(APIView):
    """
    사용자가 입력한 재료, 선호 음식, 조리 방식을 전송받아 저장(또는 임시로 ChatLog 등에 보관).
    """
    def post(self, request):
        # 예: ChatLog에 저장하거나, 별도의 모델에 저장할 수도 있음
        ingredients = request.data.get("ingredients", [])
        preferences = request.data.get("preferences", "")
        cooking_method = request.data.get("cooking_method", "")

        # 간단히 ChatLog를 생성해 예시로 저장
        user_input_str = f"재료: {ingredients}, 선호: {preferences}, 방식: {cooking_method}"
        chat_log = ChatLog.objects.create(user_input=user_input_str)

        return Response({
            "status": "success",
            "message": "입력된 재료가 저장되었습니다.",
            "chat_log_id": chat_log.id
        }, status=status.HTTP_200_OK)


# 2) 레시피 추천 - /api/recipes/recommend/ (GET)
class RecipeRecommendView(APIView):
    """
    AI(또는 간단 로직)로 추천 레시피 목록을 조회
    """
    def get(self, request):
        # 예시: 단순 전체 레시피 중 상위 5개를 추천
        qs = Recipe.objects.all()[:5]
        serializer = RecipeSerializer(qs, many=True)

        return Response({
            "status": "success",
            "recipes": serializer.data
        }, status=status.HTTP_200_OK)


# 3) 필터링 적용 - /api/recipes/filter/ (GET)
class RecipeFilterView(APIView):
    """
    Query Parameter를 받아 필터링된 레시피 목록을 반환
    ?cook_time=15-30&servings=4
    """
    def get(self, request):
        cook_time_range = request.query_params.get("cook_time", None)
        servings = request.query_params.get("servings", None)

        # cook_time_range 예: "15-30"
        filtered_qs = Recipe.objects.all()

        # 단순 예시: cook_time에 특정 문자열이 포함되면 필터링
        # 실제로는 cook_time을 정수(분)로 관리하거나, 범위 파싱 로직을 구현해야 함
        if cook_time_range:
            filtered_qs = filtered_qs.filter(cook_time__icontains=cook_time_range)
        if servings:
            filtered_qs = filtered_qs.filter(servings=servings)

        serializer = RecipeSerializer(filtered_qs, many=True)

        return Response({
            "status": "success",
            "filtered_recipes": serializer.data
        }, status=status.HTTP_200_OK)


# 4) 레시피 상세 조회 - /api/recipes/{recipe_id}/ (GET)
class RecipeDetailView(APIView):
    """
    특정 레시피 상세 정보를 반환
    """
    def get(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response({"error": "존재하지 않는 레시피입니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 5) 추천 리스트 다시 받기 - /api/recipes/recommend/refresh/ (POST)
class RecipeRecommendRefreshView(APIView):
    """
    새로운 추천 레시피 요청
    """
    def post(self, request):
        user_id = request.data.get("user_id", None)
        # user_id를 기반으로 새로운 추천 로직을 수행하거나, 임의로 다른 레시피를 추천
        # 예시: 전체 레시피 중 랜덤 3개
        qs = Recipe.objects.all().order_by('?')[:3]
        serializer = RecipeSerializer(qs, many=True)

        return Response({
            "status": "success",
            "message": "새로운 추천 리스트가 생성되었습니다.",
            "recipes": serializer.data
        }, status=status.HTTP_200_OK)

