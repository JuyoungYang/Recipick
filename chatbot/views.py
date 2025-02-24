import json
import openai
import pandas as pd
from django.conf import settings
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response  
from rest_framework import status
from recipe.utils import save_recipe_with_ai_instructions
from recipe.models import Recipe  # Recipe 모델은 새 스키마에 맞게 필드가 정의되어야 함 (CKG_NM, CKG_MTRL_CN, CKG_INBUN_NM, CKG_TIME_NM, RCP_IMG_URL, CKG_METHOD_CN)
from recipe.serializers import RecipeListSerializer
from .models import ChatLog
from django.shortcuts import get_object_or_404


# 환경 변수 로드 및 OpenAI API 키 설정
load_dotenv()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class GenerateInstructionsView(APIView):

    """
    레시피 조리방법 생성 API
    - Recipe 조회 후, AI를 통해 조리방법(CKG_METHOD_CN) 생성 및 DB 저장
    """


    def get(self, request, recipe_id):
        try:
            recipe = get_object_or_404(Recipe, id=recipe_id)


            # 만약 이미 생성된 조리방법이 있다면 DB에서 반환
            # 수정됨: recipe.instructions → recipe.CKG_METHOD_CN 사용
            if recipe.CKG_METHOD_CN:
                return Response({
                    "status": settings.STATUS_SUCCESS,
                    "recipe_name": recipe.CKG_NM,  # 수정됨: recipe.name → recipe.CKG_NM
                    "instructions": recipe.CKG_METHOD_CN,  # 수정됨
                    "source": "database",
                })

            # AI로 조리방법 생성
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            # 수정됨: 필드명을 새 DB 컬럼명에 맞게 변경
            prompt = f"""
            레시피 이름: {recipe.CKG_NM}
            재료: {recipe.CKG_MTRL_CN}
            조리 시간: {recipe.CKG_TIME_NM}
            인분: {recipe.CKG_INBUN_NM}


            위 레시피의 상세한 조리 방법을 단계별로 설명해주세요.
            각 단계는 번호를 붙여서 설명해주세요.
            """

            response = client.chat.completions.create(
                model=settings.GPT_MODEL_NAME,
                messages=[
                    {"role": "system", "content": settings.SYSTEM_RECIPE_EXPERT},
                    {"role": "user", "content": prompt},
                ],   

            )

            instructions = response.choices[0].message.content

            # 생성된 조리방법 저장
            # 수정됨: recipe.instructions → recipe.CKG_METHOD_CN 저장
            recipe.CKG_METHOD_CN = instructions

            recipe.save()

            return Response(
                {
                    "status": settings.STATUS_SUCCESS,

                    "recipe_name": recipe.CKG_NM,  # 수정됨

                    "instructions": instructions,
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
        except openai.OpenAIError as e:
            return Response(
                {
                    "status": settings.STATUS_ERROR,
                    "message": f"AI 생성 중 오류가 발생했습니다: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            return Response(
                {"status": settings.STATUS_ERROR, "message": settings.UNKNOWN_ERROR},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
    """
    사용자 메시지를 처리하는 View
    - GET: 임시 추천 레시피 목록 반환
    - POST: 사용자 입력에 따른 레시피 검색 및 AI 메뉴 추천, 채팅 로그 저장
    """

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
        """사용자 메시지 처리: 숫자 입력일 경우 상세 레시피 반환, 그렇지 않으면 AI 메뉴 추천"""
        try:
            # 숫자(1-5)로만 이루어진 입력인지 확인
            if user_message.strip().isdigit() and 1 <= int(user_message) <= 5:
                # 수정됨: 필드명을 새 DB 컬럼명에 맞게 변경 (CKG_NM, CKG_MTRL_CN, CKG_METHOD_CN)

                recipes = Recipe.objects.filter(CKG_NM__icontains=user_message)[:5]
                if recipes:
                    selected_recipe = recipes[int(user_message) - 1]
                    return {
                        "response": f"{selected_recipe.CKG_NM}의 레시피입니다:\n\n"
                                    f"재료: {selected_recipe.CKG_MTRL_CN}\n"
                                    f"조리방법: {selected_recipe.CKG_METHOD_CN}",
                        "recipes": [],
                    }

            # 일반 검색어 처리: AI를 통한 메뉴 추천

            response = client.chat.completions.create(
                model=settings.GPT_MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "사용자가 요리를 검색하면 메뉴 추천만 해주세요. 레시피는 알려주지 마세요.",
                    },
                    {"role": "user", "content": user_message},
                ],
            )
            gpt_message = response.choices[0].message.content


            # 실제 레시피 검색 (필드명을 새 DB 컬럼명에 맞게 사용)
            recipes = Recipe.objects.filter(CKG_NM__icontains=user_message)[:5]
            recipe_list = RecipeListSerializer(recipes, many=True).data

            return {
                "response": f"{gpt_message}\n\n아래 메뉴 중에서 선택해주세요!",
                "recipes": recipe_list,
            }

        except Exception as e:
            raise Exception(f"OpenAI API 호출 실패: {str(e)}")

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


    def format_error_response(self, message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
        """에러 응답 포맷팅"""
        return Response(
            {"status": settings.STATUS_ERROR, "message": message}, status=status_code
        )