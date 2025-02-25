from rest_framework import serializers
from .models import Recipe
from django.conf import settings


class RecipeInputSerializer(serializers.Serializer):
    """사용자 입력 처리 (/api/recipes/input/)"""

    ingredients = serializers.ListField(child=serializers.CharField())
    preferences = serializers.CharField()
    cooking_method = serializers.CharField()


class RecipeListSerializer(serializers.ModelSerializer):
    """레시피 목록용 직렬화 클래스"""

    # 이미지 URL을 처리하는 메서드 추가
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # 이미지 URL이 없거나 빈 문자열이면 기본 이미지 URL 설정
        if (
            not representation.get("RCP_IMG_URL")
            or not representation.get("RCP_IMG_URL").strip()
        ):
            representation["RCP_IMG_URL"] = settings.DEFAULT_RECIPE_IMAGE_PATH

        return representation

    class Meta:
        model = Recipe
        fields = [
            "id",
            "CKG_NM",
            "CKG_MTRL_CN",
            "CKG_INBUN_NM",
            "CKG_TIME_NM",
            "RCP_IMG_URL",
        ]


class FilteredRecipeSerializer(serializers.ModelSerializer):
    """필터링된 레시피 목록 조회 (/api/recipes/filter/)"""

    # 이미지 URL을 처리하는 메서드 추가 (FilteredRecipeSerializer에도 적용)
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # 이미지 URL이 필드에 있는 경우에만 처리
        if "RCP_IMG_URL" in representation:
            if (
                not representation.get("RCP_IMG_URL")
                or not representation.get("RCP_IMG_URL").strip()
            ):
                representation["RCP_IMG_URL"] = (
                    f"{settings.STATIC_URL}images/default_recipe.jpg"
                )

        return representation

    class Meta:
        model = Recipe
        fields = ["id", "CKG_NM", "CKG_TIME_NM", "CKG_INBUN_NM"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    """레시피 상세 정보용 직렬화 클래스"""

    # 이미지 URL을 처리하는 메서드 추가
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # 이미지 URL이 없거나 빈 문자열이면 기본 이미지 URL 설정
        if (
            not representation.get("RCP_IMG_URL")
            or not representation.get("RCP_IMG_URL").strip()
        ):
            representation["RCP_IMG_URL"] = (
                f"{settings.STATIC_URL}images/default_recipe.jpg"
            )

        return representation

    class Meta:
        model = Recipe
        fields = "__all__"  # 모든 필드 추가


class RefreshRecommendationSerializer(serializers.Serializer):
    """추천 레시피 새로고침 (/api/recipes/recommend/refresh/)"""

    user_id = serializers.IntegerField()
