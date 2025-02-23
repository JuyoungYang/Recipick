import json
import os
import openai
import pandas as pd
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from dotenv import load_dotenv

from .models import ChatLog
from recipe.models import Recipe
from recipe.serializers import RecipeListSerializer

# 상수 정의
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"
EMPTY_MESSAGE_ERROR = "메시지를 입력해주세요"
CHAT_SAVE_ERROR = "대화 저장에 실패했습니다."
UNKNOWN_ERROR = "알 수 없는 오류가 발생했습니다."

# 설정값
MAX_CHAT_TURNS = 5
GPT_MODEL_NAME = "gpt-4o-mini"
SYSTEM_RECIPE_EXPERT = "당신은 요리 전문가입니다."
SYSTEM_RECIPE_FINDER = "사용자가 찾는 레시피나 음식을 파악해주세요."

# 환경 변수 로드
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class RecipeGenerator:
    """레시피 생성을 담당하는 클래스"""

    def __init__(self):
        self.default_image_url = f"{settings.STATIC_URL}images/default_recipe.jpg"
        self.system_message = {"role": "system", "content": SYSTEM_RECIPE_EXPERT}

    def fill_missing_data(self, recipe_name, field_type):
        """빈 필드 데이터 생성"""
        prompts = {
            "조리시간": f"'{recipe_name}'의 예상 조리시간만 숫자로 알려주세요. (예: 30)",
            "인분": f"'{recipe_name}'의 일반적인 1회 섭취 인분 수만 숫자로 알려주세요. (예: 2)",
            "조리방법": f"'{recipe_name}'의 조리방법을 단계별로 설명해주세요.",
        }

        response = self._call_gpt_api(prompts[field_type])
        return response.choices[0].message["content"]

    def _call_gpt_api(self, prompt):
        """GPT API 호출"""
        return openai.chat.completions.create(
            model=GPT_MODEL_NAME,
            messages=[self.system_message, {"role": "user", "content": prompt}],
        )

    def process_csv_data(self, df):
        """CSV 데이터 처리"""
        for index, row in df.iterrows():
            try:
                if pd.isna(row["CKG_NM"]):
                    continue

                self._process_single_row(index, row, df)

            except Exception as e:
                print(f"Error processing recipe {row['CKG_NM']}: {str(e)}")
                continue

        return df

    def _process_single_row(self, index, row, df):
        """단일 행 처리 - 빈 필드만 AI로 채움"""
        if self._is_empty_field(row["CKG_TIME_NM"]):
            cooking_time = self.fill_missing_data(row["CKG_NM"], "조리시간")
            df.at[index, "CKG_TIME_NM"] = cooking_time

        if self._is_empty_field(row["CKG_INBUN_NM"]):
            servings = self.fill_missing_data(row["CKG_NM"], "인분")
            df.at[index, "CKG_INBUN_NM"] = servings

        if self._is_empty_field(row["CKG_MTRL_CN"]):
            cooking_method = self.fill_missing_data(row["CKG_NM"], "조리방법")
            df.at[index, "CKG_MTRL_CN"] = cooking_method

    @staticmethod
    def _is_empty_field(field):
        """필드가 비어있는지 확인"""
        return pd.isna(field) or str(field).strip() == ""


class ChatbotMessageView(APIView):
    """사용자의 메시지를 처리하는 View"""

    def __init__(self):
        super().__init__()
        self.recipe_generator = RecipeGenerator()
        self.system_message = {"role": "system", "content": SYSTEM_RECIPE_FINDER}

    def post(self, request):
        try:
            user_message = self._get_user_message(request)
            if not user_message:
                return self.format_error_response(
                    EMPTY_MESSAGE_ERROR, status.HTTP_400_BAD_REQUEST
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
        """사용자 메시지 처리"""
        chat_history = self._get_recent_chat_history(session_id)
        chat_history.append({"role": "user", "content": user_message})

        # OpenAI API 호출
        response = openai.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[
                {"role": "system", "content": "당신은 요리 전문가입니다."},
                *chat_history,
            ],
        )

        gpt_message = response.choices[0].message.content

        # 레시피 추천 (임시로 5개)
        recipes = Recipe.objects.all()[:5]
        recipe_list = RecipeListSerializer(recipes, many=True).data

        return {"response": gpt_message, "recipes": recipe_list}

    def _get_recent_chat_history(self, session_id, max_turns=MAX_CHAT_TURNS):
        """최근 대화 히스토리 조회"""
        chat_logs = ChatLog.objects.filter(session_id=session_id).order_by(
            "-created_at"
        )[:max_turns]
        return [
            item
            for log in reversed(chat_logs)
            for item in [
                {"role": "user", "content": log.user_input},
                {
                    "role": "assistant",
                    "content": json.loads(log.recommended_recipes)["response"],
                },
            ]
        ]

    def _save_chat_log(self, session_id, user_message, response_data):
        """채팅 로그 저장"""
        try:
            ChatLog.objects.create(
                session_id=session_id,
                user_input=user_message,
                recommended_recipes=json.dumps({"response": response_data}),
            )
        except Exception:
            raise Exception(CHAT_SAVE_ERROR)

    def format_success_response(self, data):
        """성공 응답 포맷팅"""
        return Response(
            {"status": STATUS_SUCCESS, "response": data}, status=status.HTTP_200_OK
        )

    def format_error_response(
        self, message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        """에러 응답 포맷팅"""
        return Response(
            {"status": STATUS_ERROR, "message": message}, status=status_code
        )
