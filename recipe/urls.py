from django.urls import path
from .views import (
    RecipeInputView, RecipeRecommendView, RecipeFilterView,
    RecipeDetailView, RecipeRecommendRefreshView
)

urlpatterns = [
    path('input/', RecipeInputView.as_view(), name='recipe-input'),               # POST
    path('recommend/', RecipeRecommendView.as_view(), name='recipe-recommend'),   # GET
    path('filter/', RecipeFilterView.as_view(), name='recipe-filter'),            # GET
    path('<int:recipe_id>/', RecipeDetailView.as_view(), name='recipe-detail'),   # GET
    path('recommend/refresh/', RecipeRecommendRefreshView.as_view(), name='recipe-recommend-refresh'),  # POST   
]  
