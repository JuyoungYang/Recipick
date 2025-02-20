from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # recipe_app
    path('api/', include('recipe_app.urls')),
    # chatbot_app
    path('api/', include('chatbot_app.urls')),
]
