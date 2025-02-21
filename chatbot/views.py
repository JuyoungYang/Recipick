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
from .serializers import ChatLogSerializer
from recipe.models import Recipe
from recipe.serializers import RecipeSerializer

# 환경 변수 로드
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# 토큰 제한을 고려하여 최근 n개의 대화만 유지하는 함수
def get_recent_chat_history(session_id, max_turns=5):
    chat_logs = ChatLog.objects.filter(session_id=session_id).order_by('-created_at')[:max_turns]
    history = []
    for log in reversed(chat_logs):  # 최신 대화가 뒤에 오도록 정렬
        history.append({"role": "user", "content": log.user_input})
        history.append({"role": "assistant", "content": json.loads(log.recommended_recipes)['response']})
    return history

class ChatbotMessageView(APIView):
    """
    사용자의 메시지를 OpenAI API에 전달 후 응답 반환 (멀티턴 지원)
    """
    def post(self, request):
        try:
            user_message = request.data.get("message", "")
            if not user_message:
                return Response({
                    "status": "error",
                    "message": "메시지를 입력해주세요"
                }, status=status.HTTP_400_BAD_REQUEST)

            session_id = request.data.get("session_id", "")

            # 최근 대화 히스토리 가져오기 (최대 5개 유지)
            chat_history = get_recent_chat_history(session_id)
            chat_history.append({"role": "user", "content": user_message})

            # OpenAI API 호출
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a helpful recipe assistant."}] + chat_history
            )
            gpt_message = response.choices[0].message["content"]

            # ChatLog 저장
            try:
                ChatLog.objects.create(
                    session_id=session_id,
                    user_input=user_message,
                    recommended_recipes=json.dumps({"response": gpt_message})
                )
            except Exception:
                return Response({
                    "status": "error",
                    "response": "대화 저장에 실패했습니다."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                "status": "success",
                "response": gpt_message
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": "error",
                "message": "알 수 없는 오류가 발생했습니다."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 빠진 데이터를 보완하는 함수
def fill_missing_data(recipe_name, missing_field):
    prompt = f"""레시피 '{recipe_name}'의 빠진 {missing_field}를 생성해주세요.
    다음과 같은 형식으로 작성해주세요:

    [조리시간 예시]
    조리시간: 5분
    양: 1인분

    [재료 예시]
    재료:
    • 밥 1공기
    • 참치캔 1개
    • 마요네즈 1큰술
    • 간장 1작은술

    [조리방법 예시]
    만드는 법:
    1. 참치캔의 기름을 빼고 그릇에 담아줘.
    2. 참치에 마요네즈, 간장, 후추, 설탕을 넣고 잘 섞어.
    3. 밥 위에 참치 마요를 올리고, 쪽파나 김 가루로 마무리해.
    4. 잘 비벼서 바로 먹으면 끝!
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 요리 전문가입니다. 주어진 형식에 맞춰 응답해주세요."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message["content"]

# 레시피 상세 설명을 보강하는 함수
def enhance_recipe_content(recipe_data):
    prompt = f"""다음 레시피의 조리법을 아래 형식에 맞춰 자세히 설명해주세요:
    레시피명: {recipe_data['CKG_NM']}

    응답 형식:
    조리시간: n분
    양: n인분
    재료:
    • 재료1 양
    • 재료2 양
    • ...

    만드는 법:
    1. 첫 번째 단계
    2. 두 번째 단계
    3. ...
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",   
        messages=[
            {"role": "system", "content": "당신은 요리 전문가입니다. 주어진 형식에 맞춰 응답해주세요."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message["content"]

# CSV 데이터 처리
def process_csv_data(df):
    for index, row in df.iterrows():
        # 조리시간이 없는 경우에만 보완
        if pd.isna(row['CKG_TIME_NM']) or row['CKG_TIME_NM'] == '':
            cooking_time = fill_missing_data(row['CKG_NM'], '조리시간')
            df.at[index, 'CKG_TIME_NM'] = cooking_time
        
        # 레시피 설명이 없는 경우에만 보강
        if pd.isna(row['CKG_IPDC']) or row['CKG_IPDC'] == '':
            enhanced_content = enhance_recipe_content(row)
            df.at[index, 'CKG_IPDC'] = enhanced_content
    
    return df   