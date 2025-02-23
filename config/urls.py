from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/recipes/", include("recipe.urls")),
    path("api/chatbot/message/", include("chatbot.urls")),
]
