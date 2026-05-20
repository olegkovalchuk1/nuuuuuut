from django.urls import path

from recipes.views import list_recipes, recipe_detail, recipes_page, sync_recipes

urlpatterns = [
    path("recipes-ui/", recipes_page, name="recipes_page"),
    path("sync-recipes/", sync_recipes, name="sync_recipes"),
    path("recipes/", list_recipes, name="list_recipes"),
    path("api/recipes/", list_recipes, name="api_list_recipes"),
    path("recipes/<int:recipe_id>/", recipe_detail, name="recipe_detail"),
    path("api/recipes/<int:recipe_id>/", recipe_detail, name="api_recipe_detail"),
]
