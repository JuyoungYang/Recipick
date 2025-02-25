from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Q
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


@api_view(["GET"])
def recommend_recipes(request):
    """AI 추천 레시피 목록 조회 - 중복 이름 없이 5개 보장, 부족하면 AI가 생성"""
    try:
        # 필터 옵션 가져오기
        time_filters = request.query_params.getlist("time_filters", [])
        serving_size = request.query_params.get("serving_size", None)
        search_query = request.query_params.get("search_query", "요리")

        # user_message에 search_query를 할당
        user_message = search_query

        # 전체 레시피 데이터 조회
        all_recipes = Recipe.objects.all()

        # 필터 적용
        if time_filters:
            time_conditions = Q()
            for time_filter in time_filters:
                if time_filter == "5분 이내":
                    time_conditions |= Q(CKG_TIME_NM__icontains="5분") | Q(
                        CKG_TIME_NM__regex=r"^[1-5]분$"
                    )
                elif time_filter == "5~15분":
                    time_conditions |= Q(CKG_TIME_NM__regex=r"^(([5-9]|1[0-5]))분$")
                elif time_filter == "15~30분":
                    time_conditions |= Q(CKG_TIME_NM__regex=r"^(1[5-9]|2[0-9]|30)분$")
                elif time_filter == "30분 이상":
                    time_conditions |= Q(
                        CKG_TIME_NM__regex=r"^([3-9][0-9]|[1-9][0-9]{2,})분$"
                    )

            all_recipes = all_recipes.filter(time_conditions)

        if serving_size:
            if serving_size == "1인분":
                all_recipes = all_recipes.filter(CKG_INBUN_NM__icontains="1인분")
            elif serving_size == "2인분":
                all_recipes = all_recipes.filter(CKG_INBUN_NM__icontains="2인분")
            elif serving_size == "4인분":
                all_recipes = all_recipes.filter(CKG_INBUN_NM__icontains="4인분")
            elif serving_size == "6인분 이상":
                all_recipes = all_recipes.filter(
                    Q(CKG_INBUN_NM__regex=r"^([6-9]|[1-9][0-9]+)인분$")
                )

        # 추천할 레시피 목록 (ID와 이름 중복 방지)
        selected_recipes = []
        selected_ids = set()
        selected_names = set()

        # 필터링된 레시피에서 랜덤 선택
        all_recipe_list = list(all_recipes)
        random.shuffle(all_recipe_list)

        for recipe in all_recipe_list:
            if recipe.id not in selected_ids and recipe.CKG_NM not in selected_names:
                selected_recipes.append(recipe)
                selected_ids.add(recipe.id)
                selected_names.add(recipe.CKG_NM)

                if len(selected_recipes) >= 5:
                    break

        # 부족한 레시피 수 계산
        missing_count = 5 - len(selected_recipes)

        # AI로 새 레시피 생성 (필터 조건 반영)
        if missing_count > 0:
            # 조리시간과 인분 기본값 설정
            default_time = None
            if time_filters:
                selected_filter = random.choice(time_filters)
                if selected_filter == "5분 이내":
                    default_time = f"{random.randint(1, 5)}분"
                elif selected_filter == "5~15분":
                    default_time = f"{random.randint(5, 15)}분"
                elif selected_filter == "15~30분":
                    default_time = f"{random.randint(15, 30)}분"
                elif selected_filter == "30분 이상":
                    default_time = f"{random.randint(30, 60)}분"

            default_servings = serving_size if serving_size else "2인분"

            # AI 레시피 생성 로직
            for i in range(missing_count):

                # AI로 새 레시피 생성
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

                prompt = f"""
                '{user_message}'와 관련된 맛있는 음식 레시피를 하나만 생성해주세요.

                조건:
                - 조리 시간은 {default_time} 이내여야 합니다.
                - 인분 수는 정확히 {default_servings}인분으로 설정해주세요.
                - 재료의 양은 {default_servings}인분에 맞게 조절해주세요.

                다음 형식으로 응답해 주세요:

                CKG_NM: [요리 이름]
                CKG_MTRL_CN: [사용된 재료 목록과 정확한 양(g, ml 등 단위 포함), 각 재료는 세로 막대(|)로 구분]
                CKG_INBUN_NM: {default_servings}
                CKG_TIME_NM: {default_time}
                """

                try:
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
                            CKG_INBUN_NM=recipe_data.get(
                                "CKG_INBUN_NM", default_servings
                            ),
                            CKG_TIME_NM=recipe_data.get(
                                "CKG_TIME_NM", default_time if default_time else "30분"
                            ),
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

                except Exception as e:
                    print(f"레시피 생성 실패: {str(e)}")
                    continue

        # 직렬화 및 반환
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
