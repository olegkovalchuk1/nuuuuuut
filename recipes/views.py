from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from recipes.models import Recipe
from recipes.services.recipe_service import fetch_and_save_recipes

MOCK_RECIPES = [
    {
        "id": 0,
        "api_id": "mock-breakfast-1",
        "name": "Омлет з овочами",
        "category": "Breakfast",
        "instructions": "Збийте яйця, додайте овочі та обсмажте на пательні.",
        "image_url": "/static/avocado-omelette.jpg",
        "calories": 320,
        "protein": 21,
        "fat": 18,
        "carbs": 16,
        "ingredients": [
            {"name": "Яйця", "grams": 120, "calories_per_100g": 155, "protein_per_100g": 13, "fat_per_100g": 11, "carbs_per_100g": 1.1},
            {"name": "Помідори", "grams": 80, "calories_per_100g": 18, "protein_per_100g": 0.9, "fat_per_100g": 0.2, "carbs_per_100g": 3.9},
            {"name": "Шпинат", "grams": 50, "calories_per_100g": 23, "protein_per_100g": 2.9, "fat_per_100g": 0.4, "carbs_per_100g": 3.6},
        ],
    },
    {
        "id": 0,
        "api_id": "mock-lunch-1",
        "name": "Боул з куркою та рисом",
        "category": "Lunch",
        "instructions": "Відваріть рис, приготуйте курку та змішайте з овочами.",
        "image_url": "/static/chicken-bowl.jpg",
        "calories": 540,
        "protein": 36,
        "fat": 15,
        "carbs": 63,
        "ingredients": [
            {"name": "Куряче філе", "grams": 150, "calories_per_100g": 165, "protein_per_100g": 31, "fat_per_100g": 3.6, "carbs_per_100g": 0},
            {"name": "Рис", "grams": 140, "calories_per_100g": 130, "protein_per_100g": 2.7, "fat_per_100g": 0.3, "carbs_per_100g": 28},
            {"name": "Овочі", "grams": 120, "calories_per_100g": 35, "protein_per_100g": 2.1, "fat_per_100g": 0.4, "carbs_per_100g": 6.5},
        ],
    },
    {
        "id": 0,
        "api_id": "mock-dinner-1",
        "name": "Салат з тунцем",
        "category": "Dinner",
        "instructions": "Змішайте тунець, яйця, овочі та легку заправку.",
        "image_url": "/static/tuna-salad.jpg",
        "calories": 390,
        "protein": 29,
        "fat": 14,
        "carbs": 24,
        "ingredients": [
            {"name": "Тунець", "grams": 90, "calories_per_100g": 132, "protein_per_100g": 28, "fat_per_100g": 1.3, "carbs_per_100g": 0},
            {"name": "Яйця", "grams": 100, "calories_per_100g": 155, "protein_per_100g": 13, "fat_per_100g": 11, "carbs_per_100g": 1.1},
            {"name": "Огірок", "grams": 80, "calories_per_100g": 15, "protein_per_100g": 0.7, "fat_per_100g": 0.1, "carbs_per_100g": 3.6},
        ],
    },
]


def _serialize_recipe(recipe):
    return {
        "id": recipe.id,
        "api_id": recipe.api_id,
        "name": recipe.name,
        "category": recipe.category,
        "instructions": recipe.instructions,
        "image_url": recipe.image_url,
        "calories": recipe.calories,
        "protein": recipe.protein,
        "fat": recipe.fat,
        "carbs": recipe.carbs,
        "ingredients": [
            {
                "name": ri.ingredient.name,
                "grams": ri.grams,
                "calories_per_100g": ri.ingredient.calories_per_100g,
                "protein_per_100g": ri.ingredient.protein_per_100g,
                "fat_per_100g": ri.ingredient.fat_per_100g,
                "carbs_per_100g": ri.ingredient.carbs_per_100g,
            }
            for ri in recipe.recipe_ingredients.all()
        ],
    }


@require_GET
def sync_recipes(request):
    query = request.GET.get("q", "chicken")
    saved = fetch_and_save_recipes(query=query)
    return JsonResponse({"status": "ok", "saved": saved, "query": query})


@require_GET
def list_recipes(request):
    query = (request.GET.get("q") or "").strip()

    try:
        limit = int(request.GET.get("limit", 50))
    except (TypeError, ValueError):
        limit = 50

    limit = max(1, min(limit, 200))

    queryset = Recipe.objects.order_by("name").prefetch_related(
        "recipe_ingredients__ingredient"
    )
    if query:
        queryset = queryset.filter(name__icontains=query)

    total = queryset.count()
    if total == 0:
        filtered = MOCK_RECIPES
        if query:
            query_lower = query.lower()
            filtered = [item for item in MOCK_RECIPES if query_lower in item["name"].lower()]
        return JsonResponse(
            {
                "count": len(filtered),
                "limit": limit,
                "results": filtered[:limit],
            }
        )

    recipes = [_serialize_recipe(recipe) for recipe in queryset[:limit]]
    return JsonResponse({"count": total, "limit": limit, "results": recipes})


@require_GET
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related("recipe_ingredients__ingredient"),
        pk=recipe_id,
    )
    return JsonResponse(_serialize_recipe(recipe))


@require_GET
def recipes_page(request):
    return render(request, "recipes.html")
