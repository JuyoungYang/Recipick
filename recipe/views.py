from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
import openai
from .models import Recipe
import random
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


# recommend_recipes 함수 수정 (paste-2.txt)
@api_view(["GET"])
def recommend_recipes(request):
    """AI 추천 레시피 목록 조회 - 중복 이름 없이 5개 보장, 부족하면 AI가 생성"""
    try:
        # 전체 레시피 데이터 조회
        all_recipes = Recipe.objects.all()

        # 추천할 레시피 목록 (ID와 이름 중복 방지)
        selected_recipes = []
        selected_ids = set()
        selected_names = set()  # 이름 중복 방지를 위한 세트 추가

        # 전체 레시피에서 랜덤 선택 (이름 중복 방지)
        all_recipe_list = list(all_recipes)
        random.shuffle(all_recipe_list)  # 목록을 랜덤하게 섞음

        for recipe in all_recipe_list:
            # ID와 이름이 모두 중복되지 않는 경우에만 추가
            if recipe.id not in selected_ids and recipe.CKG_NM not in selected_names:
                selected_recipes.append(recipe)
                selected_ids.add(recipe.id)
                selected_names.add(recipe.CKG_NM)

                # 5개가 찼으면 중단
                if len(selected_recipes) >= 5:
                    break

        # 부족한 레시피 수 계산
        missing_count = 5 - len(selected_recipes)

        # 부족한 경우 AI로 새 레시피 생성
        if missing_count > 0:
            # 기본 키워드 리스트 (다양한 레시피 생성용)
            keywords = [
                "한식",
                "양식",
                "일식",
                "중식",
                "분식",
                "디저트",
                "샐러드",
                "국",
                "찌개",
            ]

            for i in range(missing_count):
                # 이미 선택된 이름과 겹치지 않는 레시피 생성을 시도
                recipe_created = False
                max_attempts = 3  # 최대 시도 횟수 제한

                for attempt in range(max_attempts):
                    selected_keyword = random.choice(keywords)

                    # AI로 새 레시피 생성
                    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

                    prompt = f"""
                    '{selected_keyword}' 카테고리의 독특하고 맛있는 음식 레시피를 하나만 생성해주세요.
                    다음 형식으로 정확하게 응답해 주세요:
                    
                    CKG_NM: [요리 이름]
                    CKG_MTRL_CN: [사용된 재료 목록, 세로 막대(|)로 구분]
                    CKG_INBUN_NM: [인분 수, 예: 2인분]
                    CKG_TIME_NM: [조리 소요 시간, 예: 30분]
                    
                    요리 이름은 기존에 없는 독특한 이름으로 지어주세요.
                    """

                    response = client.chat.completions.create(
                        model=settings.GPT_MODEL_NAME,
                        messages=[
                            {
                                "role": "system",
                                "content": settings.SYSTEM_RECIPE_EXPERT,
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.7,
                        max_tokens=500,
                    )

                    # 생성된 응답 파싱
                    ai_recipe = response.choices[0].message.content
                    recipe_data = {}

                    # 줄별로 처리하여 필드 추출
                    for line in ai_recipe.strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            recipe_data[key] = value

                    # 레시피 이름 중복 확인
                    recipe_name = recipe_data.get("CKG_NM", f"AI 추천 레시피 {i+1}")

                    # 이름이 중복되지 않는 경우에만 저장
                    if recipe_name not in selected_names:
                        # 기본 이미지 URL 설정
                        default_image_url = settings.DEFAULT_RECIPE_IMAGE_PATH

                        # DB에 저장
                        new_recipe = Recipe.objects.create(
                            CKG_NM=recipe_name,
                            CKG_MTRL_CN=recipe_data.get("CKG_MTRL_CN", ""),
                            CKG_INBUN_NM=recipe_data.get("CKG_INBUN_NM", "2인분"),
                            CKG_TIME_NM=recipe_data.get("CKG_TIME_NM", "30분"),
                            RCP_IMG_URL=default_image_url,
                        )

                        # 조리 방법 생성 및 저장
                        instructions_prompt = f"""
                        레시피 이름: {new_recipe.CKG_NM}
                        필요한 재료: {new_recipe.CKG_MTRL_CN}
                        조리 시간: {new_recipe.CKG_TIME_NM}
                        인분: {new_recipe.CKG_INBUN_NM}
                        
                        위 레시피의 상세한 조리 방법을 단계별로 설명해주세요.
                        """

                        instructions_response = client.chat.completions.create(
                            model=settings.GPT_MODEL_NAME,
                            messages=[
                                {
                                    "role": "system",
                                    "content": settings.SYSTEM_RECIPE_EXPERT,
                                },
                                {"role": "user", "content": instructions_prompt},
                            ],
                            temperature=0.7,
                            max_tokens=1000,
                        )

                        # 조리 방법 저장
                        new_recipe.CKG_METHOD_CN = instructions_response.choices[
                            0
                        ].message.content
                        new_recipe.save()

                        # 결과 목록에 추가
                        selected_recipes.append(new_recipe)
                        selected_names.add(recipe_name)
                        recipe_created = True
                        break

                # 최대 시도 횟수를 초과해도 생성 실패한 경우
                if not recipe_created:
                    unique_name = f"AI 추천 레시피 {i+1} ({selected_keyword})"
                    # 기본 이미지 URL 설정
                    default_image_url = settings.DEFAULT_RECIPE_IMAGE_PATH

                    # 기본 레시피 생성
                    new_recipe = Recipe.objects.create(
                        CKG_NM=unique_name,
                        CKG_MTRL_CN="다양한 식재료",
                        CKG_INBUN_NM="2인분",
                        CKG_TIME_NM="30분",
                        RCP_IMG_URL=default_image_url,
                    )

                    # 간단한 조리방법 생성
                    new_recipe.CKG_METHOD_CN = (
                        f"{selected_keyword} 스타일의 요리를 만듭니다."
                    )
                    new_recipe.save()

                    # 결과 목록에 추가
                    selected_recipes.append(new_recipe)
                    selected_names.add(unique_name)

        # 직렬화
        serializer = RecipeListSerializer(selected_recipes, many=True)

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


def get_recipe_image_url(recipe):
    """레시피의 이미지 URL을 반환, 없으면 기본 이미지 반환"""
    if recipe.RCP_IMG_URL and recipe.RCP_IMG_URL.strip():
        return recipe.RCP_IMG_URL
    else:
        return f"{settings.STATIC_URL}images/default_recipe.jpg"
