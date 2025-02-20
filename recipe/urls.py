from django.urls import path
from .views import (
    RecipeInputView, RecipeRecommendView, RecipeFilterView,
    RecipeDetailView, RecipeRecommendRefreshView
)

urlpatterns = [
    path('recipes/input/', RecipeInputView.as_view(), name='recipe-input'),               # POST
    path('recipes/recommend/', RecipeRecommendView.as_view(), name='recipe-recommend'),   # GET
    path('recipes/filter/', RecipeFilterView.as_view(), name='recipe-filter'),            # GET
    path('recipes/<int:recipe_id>/', RecipeDetailView.as_view(), name='recipe-detail'),   # GET
    path('recipes/recommend/refresh/', RecipeRecommendRefreshView.as_view(), name='recipe-recommend-refresh'),  # POST   
]   
