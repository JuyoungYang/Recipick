from django.urls import path
from .views import ChatbotMessageView

urlpatterns = [
    path('chatbot/message/', ChatbotMessageView.as_view(), name='chatbot-message'),  # POST
]
