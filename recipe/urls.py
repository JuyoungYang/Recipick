from django.urls import path
from . import views

app_name = "recipe"

urlpatterns = [
    path("input/", views.input_ingredients, name="recipe-input"),
    path("recommend/", views.recommend_recipes, name="recipe-recommend"),
    path("filter/", views.filter_recipes, name="recipe-filter"),
    path("<int:recipe_id>/", views.recipe_detail, name="recipe-detail"),
    path("recommend/refresh/", views.refresh_recommendations, name="recipe-refresh"),
    path(
        "generate-instructions/<int:recipe_id>/",
        views.GenerateInstructionsView.as_view(),
        name="generate-instructions",
    ),
]
