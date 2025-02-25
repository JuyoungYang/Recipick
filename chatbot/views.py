import json
import openai
import pandas as pd
from django.conf import settings
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from recipe.utils import save_recipe_with_ai_instructions
from recipe.models import (
    Recipe,
)  # Recipe 모델은 새 스키마에 맞게 필드가 정의되어야 함 (CKG_NM, CKG_MTRL_CN, CKG_INBUN_NM, CKG_TIME_NM, RCP_IMG_URL, CKG_METHOD_CN)
from recipe.serializers import RecipeListSerializer
from .models import ChatLog
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
import random


# 환경 변수 로드 및 OpenAI API 키 설정
load_dotenv()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class GenerateInstructionsView(APIView):
    """
    레시피 조리방법 생성 API - recipe 앱의 API로 리디렉션
    """

    def get(self, request, recipe_id):
        # recipe 앱의 API로 리디렉션
        return redirect(f"/api/recipes/generate-instructions/{recipe_id}/")


class RecipeGenerator:
    """
    레시피 생성을 담당하는 클래스
    - CSV 데이터의 빈 필드를 AI를 통해 채워 새 DB 컬럼(CKG_TIME_NM, CKG_INBUN_NM, CKG_METHOD_CN)에 저장
    """

    def __init__(self):
        self.default_image_url = f"{settings.STATIC_URL}images/default_recipe.jpg"
        self.system_message = {
            "role": "system",
            "content": settings.SYSTEM_RECIPE_EXPERT,
        }

    def fill_missing_data(self, recipe_name, field_type):
        """빈 필드 데이터 생성 (조리시간, 인분, 조리방법)"""
        prompts = {
            "조리시간": f"'{recipe_name}'의 예상 조리시간만 숫자로 알려주세요. (예: 30)",
            "인분": f"'{recipe_name}'의 일반적인 1회 섭취 인분 수만 숫자로 알려주세요. (예: 2)",
            "조리방법": f"'{recipe_name}'의 조리방법을 단계별로 설명해주세요.",
        }

        response = self._call_gpt_api(prompts[field_type])
        return response.choices[0].message.content

    def _call_gpt_api(self, prompt):
        """GPT API 호출"""
        try:
            response = client.chat.completions.create(
                model=settings.GPT_MODEL_NAME,
                messages=[self.system_message, {"role": "user", "content": prompt}],
            )
            return response
        except Exception as e:
            raise Exception(f"OpenAI API 호출 실패: {str(e)}")

    def process_csv_data(self, df):
        """CSV 데이터 처리: 각 행의 빈 필드 채우기"""
        for index, row in df.iterrows():
            try:
                if pd.isna(row["CKG_NM"]):
                    continue
                self._process_single_row(index, row, df)
            except Exception as e:
                print(f"Error processing recipe {row['CKG_NM']}: {str(e)}")
        return df

    def _process_single_row(self, index, row, df):
        """단일 행 처리 - 빈 필드만 AI로 채움"""
        if self._is_empty_field(row["CKG_TIME_NM"]):
            cooking_time = self.fill_missing_data(row["CKG_NM"], "조리시간")
            df.at[index, "CKG_TIME_NM"] = cooking_time

        if self._is_empty_field(row["CKG_INBUN_NM"]):
            servings = self.fill_missing_data(row["CKG_NM"], "인분")
            df.at[index, "CKG_INBUN_NM"] = servings

        # 수정됨: 재료(CKG_MTRL_CN)가 아닌 AI 생성 조리방법 컬럼(CKG_METHOD_CN) 업데이트
        if self._is_empty_field(row["CKG_METHOD_CN"]):
            cooking_method = self.fill_missing_data(row["CKG_NM"], "조리방법")
            df.at[index, "CKG_METHOD_CN"] = cooking_method

    @staticmethod
    def _is_empty_field(field):
        """필드가 비어있는지 확인"""
        return pd.isna(field) or str(field).strip() == ""


class ChatbotMessageView(APIView):
    def get(self, request):
        # 수정: 정확히 5개의 추천 레시피 목록 반환
        recipes = Recipe.objects.all()[:5]
        recipe_list = RecipeListSerializer(recipes, many=True).data
        return Response(
            {"status": "success", "response": {"recipes": recipe_list[:5]}},
            status=status.HTTP_200_OK,
        )

    def __init__(self):
        super().__init__()
        self.recipe_generator = RecipeGenerator()
        self.system_message = {
            "role": "system",
            "content": settings.SYSTEM_RECIPE_FINDER,
        }

    def get(self, request):
        """GET 요청: 5개의 추천 레시피 목록 반환"""
        recipes = Recipe.objects.all()[:5]
        recipe_list = RecipeListSerializer(recipes, many=True).data
        return Response(
            {"status": "success", "response": {"recipes": recipe_list}},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """POST 요청: 사용자 메시지 처리 및 응답 생성"""

        try:
            user_message = self._get_user_message(request)
            if not user_message:
                return self.format_error_response(
                    settings.EMPTY_MESSAGE_ERROR, status.HTTP_400_BAD_REQUEST
                )

            session_id = request.data.get("session_id", "")
            response_data = self._process_user_message(user_message, session_id)

            self._save_chat_log(session_id, user_message, response_data)
            return self.format_success_response(response_data)

        except Exception as e:
            return self.format_error_response(str(e))

    def _get_user_message(self, request):
        """사용자 메시지 추출"""
        return request.data.get("message", "")

    def _process_user_message(self, user_message, session_id):
        try:
            # 유저 메시지로 검색할 키워드 추출
            search_terms = [
                term.strip() for term in user_message.split() if len(term.strip()) > 0
            ]

            # DB에서 레시피 검색 (ID와 이름 중복 없이)
            recipe_list = []
            found_recipe_ids = set()  # ID 중복 방지
            found_recipe_names = set()  # 이름 중복 방지

            # 전체 메시지로 먼저 검색
            recipes = Recipe.objects.filter(CKG_NM__icontains=user_message)
            for recipe in recipes:
                if (
                    recipe.id not in found_recipe_ids
                    and recipe.CKG_NM not in found_recipe_names
                    and len(recipe_list) < 5
                ):
                    found_recipe_ids.add(recipe.id)
                    found_recipe_names.add(recipe.CKG_NM)
                    recipe_list.append(RecipeListSerializer(recipe).data)

            # 단어별 검색으로 더 찾기
            if len(recipe_list) < 5:
                for term in search_terms:
                    if len(term) < 2:  # 너무 짧은 검색어 건너뛰기
                        continue

                    # 이름으로 검색
                    name_recipes = Recipe.objects.filter(CKG_NM__icontains=term)
                    for recipe in name_recipes:
                        if (
                            recipe.id not in found_recipe_ids
                            and recipe.CKG_NM not in found_recipe_names
                            and len(recipe_list) < 5
                        ):
                            found_recipe_ids.add(recipe.id)
                            found_recipe_names.add(recipe.CKG_NM)
                            recipe_list.append(RecipeListSerializer(recipe).data)

                    # 재료로 검색
                    ingredient_recipes = Recipe.objects.filter(
                        CKG_MTRL_CN__icontains=term
                    )
                    for recipe in ingredient_recipes:
                        if (
                            recipe.id not in found_recipe_ids
                            and recipe.CKG_NM not in found_recipe_names
                            and len(recipe_list) < 5
                        ):
                            found_recipe_ids.add(recipe.id)
                            found_recipe_names.add(recipe.CKG_NM)
                            recipe_list.append(RecipeListSerializer(recipe).data)

                    # 충분히 찾았으면 중단
                    if len(recipe_list) >= 5:
                        break

            # 5개 미만이면 AI로 생성하여 DB에 저장 후 추가
            if len(recipe_list) < 5:
                missing_count = 5 - len(recipe_list)
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

                for i in range(missing_count):
                    # 검색어를 기반으로 키워드 선택
                    search_keyword = (
                        random.choice(search_terms)
                        if search_terms
                        else user_message[:10]
                    )

                    # 이미 선택된 이름과 겹치지 않는 레시피 생성을 시도
                    recipe_created = False
                    max_attempts = 3  # 최대 시도 횟수 제한

                    for attempt in range(max_attempts):
                        # AI로 새 레시피 생성
                        prompt = f"""
                        '{search_keyword}' 관련된 맛있는 음식 레시피를 하나만 생성해주세요.
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
                        recipe_name = recipe_data.get(
                            "CKG_NM", f"{search_keyword} 추천 레시피"
                        )

                        # 이름이 중복되지 않는 경우에만 저장
                        if recipe_name not in found_recipe_names:
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
                            recipe_data = RecipeListSerializer(new_recipe).data
                            recipe_list.append(recipe_data)
                            found_recipe_names.add(recipe_name)
                            recipe_created = True
                            break

                    # 최대 시도 횟수를 초과해도 생성 실패한 경우
                    if not recipe_created:
                        unique_name = f"{search_keyword} 추천 레시피 {i+1}"
                        # 이미 해당 이름이 있는지 확인
                        if unique_name in found_recipe_names:
                            unique_name = f"{search_keyword} 추천 레시피 {i+1} - {random.randint(1000, 9999)}"

                        # 기본 이미지 URL 설정
                        default_image_url = settings.DEFAULT_RECIPE_IMAGE_PATH

                        # 기본 레시피 생성
                        new_recipe = Recipe.objects.create(
                            CKG_NM=unique_name,
                            CKG_MTRL_CN=f"{search_keyword}|다양한 식재료",
                            CKG_INBUN_NM="2인분",
                            CKG_TIME_NM="30분",
                            RCP_IMG_URL=default_image_url,
                        )

                        # 간단한 조리방법 생성
                        new_recipe.CKG_METHOD_CN = (
                            f"{search_keyword}를 활용한 요리입니다."
                        )
                        new_recipe.save()

                        # 결과 목록에 추가
                        recipe_data = RecipeListSerializer(new_recipe).data
                        recipe_list.append(recipe_data)
                        found_recipe_names.add(unique_name)

            return {
                "response": "아래 메뉴 중에서 선택해주세요!",
                "recipes": recipe_list,
            }

        except Exception as e:
            raise Exception(f"레시피 검색 실패: {str(e)}")

    def _get_recent_chat_history(self, session_id, max_turns=settings.MAX_CHAT_TURNS):
        """최근 채팅 기록 불러오기 (최대 max_turns 만큼)"""
        chat_logs = ChatLog.objects.filter(session_id=session_id).order_by(
            "-timestamp"  # created_at → timestamp
        )[:max_turns]
        history = []
        for log in reversed(chat_logs):
            history.extend(
                [
                    {
                        "role": "user" if log.is_user else "assistant",
                        "content": log.message,
                    }
                ]
            )
        return history

    def _save_chat_log(self, session_id, user_message, response_data):
        """채팅 로그 저장: 사용자와 AI 메시지 각각 별도 저장"""
        try:
            # 사용자 메시지 저장
            ChatLog.objects.create(
                session_id=session_id,
                message=user_message,  # user_input → message
                is_user=True,
            )

            # AI 응답 저장
            ChatLog.objects.create(
                session_id=session_id,
                message=response_data["response"],  # recommended_recipes → message
                is_user=False,
            )
        except Exception:
            raise Exception(settings.CHAT_SAVE_ERROR)

    def format_success_response(self, data):
        """성공 응답 포맷팅"""
        return Response(
            {"status": settings.STATUS_SUCCESS, "response": data},
            status=status.HTTP_200_OK,
        )

    def format_error_response(
        self, message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        """에러 응답 포맷팅"""
        return Response(
            {"status": settings.STATUS_ERROR, "message": message}, status=status_code
        )
