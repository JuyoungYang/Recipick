import json
from django.conf import settings     
from rest_framework.views import APIView  
from rest_framework.response import Response   
from rest_framework import status   

import openai  # pip install openai

from .models import ChatLog
from .serializers import ChatLogSerializer
from recipe.models import Recipe
from recipe.serializers import RecipeSerializer

# 6) OpenAI 챗봇 응답 - /api/chatbot/message/ (POST)
class ChatbotMessageView(APIView):   
    """
    사용자의 메시지를 OpenAI API에 전달 후 응답 반환
    """
    def post(self, request):
        user_message = request.data.get("message", "")
        session_id = request.data.get("session_id", "")

        # 실제 GPT-4 API 호출 예시
        # openai.api_key = settings.OPENAI_API_KEY
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": "You are a helpful recipe assistant."},
        #         {"role": "user", "content": user_message}
        #     ]
        # )
        # gpt_message = response.choices[0].message["content"]

        # 데모이므로 실제 호출 대신 가짜 응답
        gpt_message = f"추천 레시피 예시: 감자전, 감자볶음, 감자탕. (session_id={session_id})"

        # ChatLog 저장
        chat_log = ChatLog.objects.create(
            user_input=user_message,
            recommended_recipes=json.dumps({"response": gpt_message})
        )

        return Response({
            "status": "success",
            "response": gpt_message
        }, status=status.HTTP_200_OK)
