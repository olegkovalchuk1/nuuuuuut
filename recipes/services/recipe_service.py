import json
import logging
import re
from fractions import Fraction
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.db import transaction

from recipes.models import Ingredient, Recipe, RecipeIngredient

logger = logging.getLogger(__name__)


# Словник харчової цінності на 100г: {kcal, protein, fat, carbs}
NUTRITION_DATA = {
    "anchovy": {"kcal": 210, "p": 29, "f": 10, "c": 0},
    "apple": {"kcal": 52, "p": 0.3, "f": 0.2, "c": 14},
    "asparagus": {"kcal": 20, "p": 2.2, "f": 0.1, "c": 3.9},
    "avocado": {"kcal": 160, "p": 2, "f": 15, "c": 9},
    "bacon": {"kcal": 541, "p": 37, "f": 42, "c": 1.4},
    "banana": {"kcal": 89, "p": 1.1, "f": 0.3, "c": 23},
    "barley": {"kcal": 123, "p": 2.3, "f": 0.4, "c": 28},
    "basil": {"kcal": 23, "p": 3.2, "f": 0.6, "c": 2.7},
    "bay leaf": {"kcal": 313, "p": 7.6, "f": 8.4, "c": 75},
    "beans": {"kcal": 127, "p": 9, "f": 0.5, "c": 23},
    "beef": {"kcal": 250, "p": 26, "f": 15, "c": 0},
    "beet": {"kcal": 43, "p": 1.6, "f": 0.2, "c": 10},
    "bell pepper": {"kcal": 31, "p": 1, "f": 0.3, "c": 6},
    "black beans": {"kcal": 132, "p": 8.9, "f": 0.5, "c": 24},
    "blueberry": {"kcal": 57, "p": 0.7, "f": 0.3, "c": 14},
    "bread": {"kcal": 265, "p": 9, "f": 3.2, "c": 49},
    "broccoli": {"kcal": 34, "p": 2.8, "f": 0.4, "c": 7},
    "brown rice": {"kcal": 111, "p": 2.6, "f": 0.9, "c": 23},
    "brussels sprouts": {"kcal": 43, "p": 3.4, "f": 0.3, "c": 9},
    "bulgur": {"kcal": 83, "p": 3, "f": 0.2, "c": 18},
    "butter": {"kcal": 717, "p": 0.9, "f": 81, "c": 0.1},
    "cabbage": {"kcal": 25, "p": 1.3, "f": 0.1, "c": 6},
    "capers": {"kcal": 23, "p": 2.4, "f": 0.9, "c": 5},
    "carrot": {"kcal": 41, "p": 0.9, "f": 0.2, "c": 10},
    "cashew": {"kcal": 553, "p": 18, "f": 44, "c": 30},
    "cauliflower": {"kcal": 25, "p": 1.9, "f": 0.3, "c": 5},
    "celery": {"kcal": 16, "p": 0.7, "f": 0.2, "c": 3},
    "cheese": {"kcal": 402, "p": 25, "f": 33, "c": 1.3},
    "chia seed": {"kcal": 486, "p": 17, "f": 31, "c": 42},
    "chickpea": {"kcal": 164, "p": 8.9, "f": 2.6, "c": 27},
    "chicken": {"kcal": 165, "p": 31, "f": 3.6, "c": 0},
    "chicken stock": {"kcal": 15, "p": 1.1, "f": 0.5, "c": 1.1},
    "chili": {"kcal": 40, "p": 1.9, "f": 0.4, "c": 9},
    "chili powder": {"kcal": 282, "p": 13, "f": 14, "c": 50},
    "cinnamon": {"kcal": 247, "p": 4, "f": 1.2, "c": 81},
    "coconut milk": {"kcal": 230, "p": 2.3, "f": 24, "c": 6},
    "corn": {"kcal": 96, "p": 3.4, "f": 1.5, "c": 21},
    "couscous": {"kcal": 112, "p": 3.8, "f": 0.2, "c": 23},
    "cream": {"kcal": 340, "p": 2, "f": 36, "c": 2.8},
    "cream cheese": {"kcal": 342, "p": 6, "f": 34, "c": 4},
    "cucumber": {"kcal": 15, "p": 0.7, "f": 0.1, "c": 3.6},
    "cumin": {"kcal": 375, "p": 18, "f": 22, "c": 44},
    "curry powder": {"kcal": 325, "p": 14, "f": 14, "c": 56},
    "dates": {"kcal": 282, "p": 2.5, "f": 0.4, "c": 75},
    "dill": {"kcal": 43, "p": 3.5, "f": 1.1, "c": 7},
    "duck": {"kcal": 337, "p": 19, "f": 28, "c": 0},
    "egg": {"kcal": 155, "p": 13, "f": 11, "c": 1.1},
    "eggplant": {"kcal": 25, "p": 1, "f": 0.2, "c": 6},
    "feta": {"kcal": 264, "p": 14, "f": 21, "c": 4},
    "fish": {"kcal": 206, "p": 22, "f": 12, "c": 0},
    "flax seed": {"kcal": 534, "p": 18, "f": 42, "c": 29},
    "flour": {"kcal": 364, "p": 10, "f": 1, "c": 76},
    "garlic": {"kcal": 149, "p": 6.4, "f": 0.5, "c": 33},
    "ginger": {"kcal": 80, "p": 1.8, "f": 0.8, "c": 18},
    "goat cheese": {"kcal": 364, "p": 22, "f": 30, "c": 0.1},
    "grape": {"kcal": 69, "p": 0.7, "f": 0.2, "c": 18},
    "green beans": {"kcal": 31, "p": 1.8, "f": 0.2, "c": 7},
    "ham": {"kcal": 145, "p": 21, "f": 6, "c": 1.5},
    "honey": {"kcal": 304, "p": 0.3, "f": 0, "c": 82},
    "kale": {"kcal": 49, "p": 4.3, "f": 0.9, "c": 9},
    "kiwi": {"kcal": 61, "p": 1.1, "f": 0.5, "c": 15},
    "lamb": {"kcal": 294, "p": 25, "f": 21, "c": 0},
    "leek": {"kcal": 61, "p": 1.5, "f": 0.3, "c": 14},
    "lentils": {"kcal": 116, "p": 9, "f": 0.4, "c": 20},
    "lemon": {"kcal": 29, "p": 1.1, "f": 0.3, "c": 9},
    "lettuce": {"kcal": 15, "p": 1.4, "f": 0.2, "c": 2.9},
    "lime": {"kcal": 30, "p": 0.7, "f": 0.2, "c": 11},
    "mayonnaise": {"kcal": 680, "p": 1, "f": 75, "c": 0.6},
    "milk": {"kcal": 60, "p": 3.2, "f": 3.3, "c": 4.8},
    "millet": {"kcal": 119, "p": 3.5, "f": 1, "c": 23},
    "mint": {"kcal": 44, "p": 3.3, "f": 0.7, "c": 8},
    "mushroom": {"kcal": 22, "p": 3.1, "f": 0.3, "c": 3.3},
    "mustard": {"kcal": 66, "p": 4.4, "f": 4, "c": 8},
    "noodles": {"kcal": 138, "p": 4.5, "f": 2.1, "c": 25},
    "nutmeg": {"kcal": 525, "p": 5.8, "f": 36, "c": 49},
    "oats": {"kcal": 389, "p": 17, "f": 7, "c": 66},
    "oil": {"kcal": 884, "p": 0, "f": 100, "c": 0},
    "olive": {"kcal": 115, "p": 0.8, "f": 11, "c": 6},
    "olive oil": {"kcal": 884, "p": 0, "f": 100, "c": 0},
    "onion": {"kcal": 40, "p": 1.1, "f": 0.1, "c": 9},
    "orange": {"kcal": 47, "p": 0.9, "f": 0.1, "c": 12},
    "oregano": {"kcal": 265, "p": 9, "f": 4.3, "c": 69},
    "parmesan": {"kcal": 431, "p": 38, "f": 29, "c": 4.1},
    "parsley": {"kcal": 36, "p": 3, "f": 0.8, "c": 6},
    "pasta": {"kcal": 131, "p": 5, "f": 1.1, "c": 25},
    "peanut": {"kcal": 567, "p": 26, "f": 49, "c": 16},
    "peanut butter": {"kcal": 588, "p": 25, "f": 50, "c": 20},
    "pear": {"kcal": 57, "p": 0.4, "f": 0.1, "c": 15},
    "peas": {"kcal": 81, "p": 5.4, "f": 0.4, "c": 14},
    "pepper": {"kcal": 31, "p": 1, "f": 0.3, "c": 6},
    "pineapple": {"kcal": 50, "p": 0.5, "f": 0.1, "c": 13},
    "pistachio": {"kcal": 562, "p": 20, "f": 45, "c": 28},
    "pork": {"kcal": 242, "p": 27, "f": 14, "c": 0},
    "potato": {"kcal": 77, "p": 2, "f": 0.1, "c": 17},
    "pumpkin": {"kcal": 26, "p": 1, "f": 0.1, "c": 6.5},
    "quinoa": {"kcal": 120, "p": 4.4, "f": 1.9, "c": 21},
    "radish": {"kcal": 16, "p": 0.7, "f": 0.1, "c": 3.4},
    "raisins": {"kcal": 299, "p": 3.1, "f": 0.5, "c": 79},
    "rice": {"kcal": 130, "p": 2.7, "f": 0.3, "c": 28},
    "rosemary": {"kcal": 131, "p": 3.3, "f": 5.9, "c": 21},
    "salmon": {"kcal": 208, "p": 20, "f": 13, "c": 0},
    "salt": {"kcal": 0, "p": 0, "f": 0, "c": 0},
    "sausage": {"kcal": 301, "p": 12, "f": 27, "c": 2},
    "sesame seed": {"kcal": 573, "p": 18, "f": 50, "c": 23},
    "shrimp": {"kcal": 99, "p": 24, "f": 0.3, "c": 0.2},
    "sour cream": {"kcal": 193, "p": 2.1, "f": 19, "c": 4.6},
    "soy sauce": {"kcal": 53, "p": 8, "f": 0.6, "c": 4.9},
    "spinach": {"kcal": 23, "p": 2.9, "f": 0.4, "c": 3.6},
    "sugar": {"kcal": 387, "p": 0, "f": 0, "c": 100},
    "sunflower seed": {"kcal": 584, "p": 21, "f": 51, "c": 20},
    "sweet potato": {"kcal": 86, "p": 1.6, "f": 0.1, "c": 20},
    "thyme": {"kcal": 101, "p": 5.6, "f": 1.7, "c": 24},
    "tofu": {"kcal": 76, "p": 8, "f": 4.8, "c": 1.9},
    "tomato": {"kcal": 18, "p": 0.9, "f": 0.2, "c": 3.9},
    "tuna": {"kcal": 132, "p": 28, "f": 1, "c": 0},
    "turkey": {"kcal": 189, "p": 29, "f": 7, "c": 0},
    "vanilla": {"kcal": 288, "p": 0.1, "f": 0.1, "c": 13},
    "walnut": {"kcal": 654, "p": 15, "f": 65, "c": 14},
    "watermelon": {"kcal": 30, "p": 0.6, "f": 0.2, "c": 8},
    "white rice": {"kcal": 130, "p": 2.7, "f": 0.3, "c": 28},
    "wine": {"kcal": 85, "p": 0.1, "f": 0, "c": 2.6},
    "yogurt": {"kcal": 59, "p": 10, "f": 0.4, "c": 3.6},
    "zucchini": {"kcal": 17, "p": 1.2, "f": 0.3, "c": 3.1},
}

MEASURE_TO_GRAMS = {
    "cup": 240,
    "cups": 240,
    "tbsp": 15,
    "tablespoon": 15,
    "tablespoons": 15,
    "tsp": 5,
    "teaspoon": 5,
    "teaspoons": 5,
    "pinch": 1,
    "pinches": 1,
    "dash": 1,
    "slice": 25,
    "slices": 25,
    "clove": 5,
    "cloves": 5,
    "piece": 100,
    "pieces": 100,
    "fillet": 170,
    "fillets": 170,
    "can": 400,
    "cans": 400,
    "oz": 28,
    "ounce": 28,
    "ounces": 28,
    "lb": 454,
    "pound": 454,
    "pounds": 454,
    "g": 1,
    "gram": 1,
    "grams": 1,
    "kg": 1000,
    "ml": 1,
    "l": 1000,
    "liter": 1000,
    "liters": 1000,
}

_FRACTION_REPLACEMENTS = {
    "\u00bd": "1/2",
    "\u2153": "1/3",
    "\u2154": "2/3",
    "\u00bc": "1/4",
    "\u00be": "3/4",
}

_ALIASES = {
    "all purpose flour": "flour",
    "all-purpose flour": "flour",
    "baby spinach": "spinach",
    "beef mince": "beef",
    "beef stock": "beef",
    "bell pepper": "pepper",
    "black pepper": "pepper",
    "brown rice": "rice",
    "brown sugar": "sugar",
    "caster sugar": "sugar",
    "chicken breast": "chicken",
    "chicken breasts": "chicken",
    "chicken thigh": "chicken",
    "chicken thighs": "chicken",
    "chicken stock": "chicken stock",
    "chilli powder": "chili powder",
    "cilantro": "parsley",
    "coriander leaves": "parsley",
    "double cream": "cream",
    "egg yolk": "egg",
    "egg yolks": "egg",
    "eggs": "egg",
    "extra virgin olive oil": "olive oil",
    "garlic clove": "garlic",
    "garlic cloves": "garlic",
    "green pepper": "pepper",
    "ground beef": "beef",
    "heavy cream": "cream",
    "icing sugar": "sugar",
    "kidney beans": "beans",
    "lemon juice": "lemon",
    "lime juice": "lime",
    "minced beef": "beef",
    "olive oil": "oil",
    "onions": "onion",
    "plain flour": "flour",
    "potatoes": "potato",
    "red onion": "onion",
    "red pepper": "pepper",
    "sea salt": "salt",
    "self raising flour": "flour",
    "self-raising flour": "flour",
    "spring onion": "onion",
    "spring onions": "onion",
    "tomatoes": "tomato",
    "vegetable oil": "oil",
    "white sugar": "sugar",
    "whole milk": "milk",
}


def _to_float(value):
    token = value.strip()
    if not token:
        return None
    if re.fullmatch(r"\d+(\.\d+)?", token):
        return float(token)
    if re.fullmatch(r"\d+-\d+", token):
        return float(token.split("-")[0])
    if re.fullmatch(r"\d+/\d+", token):
        return float(Fraction(token))
    return None


def _normalize_text(value):
    normalized = value.lower().strip()
    for unicode_frac, plain in _FRACTION_REPLACEMENTS.items():
        normalized = normalized.replace(unicode_frac, plain)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _normalize_ingredient(ingredient):
    if not ingredient:
        return ""

    ingredient = re.sub(r"[^a-zA-Z\s]", " ", ingredient.lower())
    ingredient = re.sub(r"\s+", " ", ingredient).strip()

    if ingredient in _ALIASES:
        return _ALIASES[ingredient]

    for alias, base_name in _ALIASES.items():
        if alias in ingredient:
            return base_name

    if ingredient.endswith("es") and ingredient[:-2] in NUTRITION_DATA:
        return ingredient[:-2]
    if ingredient.endswith("s") and ingredient[:-1] in NUTRITION_DATA:
        return ingredient[:-1]
    return ingredient


def _merge_ingredients(ingredients_list):
    merged = {}
    for item in ingredients_list:
        ingredient = _normalize_ingredient((item.get("ingredient") or "").strip())
        grams = float(item.get("grams") or 0)
        if not ingredient or grams <= 0:
            continue
        merged[ingredient] = merged.get(ingredient, 0.0) + grams
    return [{"ingredient": key, "grams": round(value, 2)} for key, value in merged.items()]


def parse_ingredient(text):
    normalized = _normalize_text(text)
    if not normalized:
        return {"ingredient": "", "grams": 0}

    tokens = normalized.split()
    idx = 0
    quantity = None

    first = _to_float(tokens[0])
    if first is not None:
        quantity = first
        idx = 1
        if idx < len(tokens):
            second = _to_float(tokens[idx])
            if second is not None and "/" in tokens[idx]:
                quantity += second
                idx += 1
    elif tokens[0] in ("a", "an"):
        quantity = 1.0
        idx = 1

    measure = None
    if idx < len(tokens):
        candidate = tokens[idx].rstrip(".")
        if candidate in MEASURE_TO_GRAMS:
            measure = candidate
            idx += 1

    if quantity is None and tokens[0] in MEASURE_TO_GRAMS:
        quantity = 1.0
        measure = tokens[0]
        idx = 1

    if quantity is None:
        quantity = 1.0

    ingredient_text = " ".join(tokens[idx:]).strip()
    ingredient_name = _normalize_ingredient(ingredient_text)

    if measure:
        grams = quantity * MEASURE_TO_GRAMS[measure]
    else:
        grams = quantity * 100

    return {"ingredient": ingredient_name, "grams": round(grams, 2)}


def get_ingredients(meal):
    ingredients = []
    for i in range(1, 21):
        ingredient_name = (meal.get(f"strIngredient{i}") or "").strip()
        if not ingredient_name:
            continue
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        parsed = parse_ingredient(f"{measure} {ingredient_name}".strip())
        if not parsed["ingredient"]:
            parsed["ingredient"] = _normalize_ingredient(ingredient_name)
        ingredients.append(parsed)
    return ingredients


def _nutrition_per_100g(ingredient):
    ingredient = ingredient.lower().strip()
    if ingredient in NUTRITION_DATA:
        return NUTRITION_DATA[ingredient]

    for key, data in NUTRITION_DATA.items():
        if key in ingredient or ingredient in key:
            return data
    # Дефолтні значення, якщо не знайдено
    return {"kcal": 100, "p": 5, "f": 2, "c": 15}


def calculate_nutrition(ingredients_list):
    total = {"kcal": 0.0, "p": 0.0, "f": 0.0, "c": 0.0}
    for item in _merge_ingredients(ingredients_list):
        ingredient = (item.get("ingredient") or "").strip()
        grams = float(item.get("grams") or 0)
        if not ingredient or grams <= 0:
            continue
        data = _nutrition_per_100g(ingredient)
        total["kcal"] += grams * data["kcal"] / 100.0
        total["p"] += grams * data["p"] / 100.0
        total["f"] += grams * data["f"] / 100.0
        total["c"] += grams * data["c"] / 100.0

    return {k: round(v, 1) for k, v in total.items()}


def _save_recipe_ingredients(recipe, ingredients_list):
    merged = _merge_ingredients(ingredients_list)
    RecipeIngredient.objects.filter(recipe=recipe).delete()

    rows = []
    for item in merged:
        ingredient_name = item["ingredient"]
        grams = float(item["grams"])
        data = _nutrition_per_100g(ingredient_name)
        
        ingredient_obj, created = Ingredient.objects.get_or_create(
            name=ingredient_name,
            defaults={
                "calories_per_100g": data["kcal"],
                "protein_per_100g": data["p"],
                "fat_per_100g": data["f"],
                "carbs_per_100g": data["c"],
            },
        )
        if not created:
            updated = False
            if ingredient_obj.calories_per_100g is None:
                ingredient_obj.calories_per_100g = data["kcal"]
                updated = True
            if ingredient_obj.protein_per_100g is None:
                ingredient_obj.protein_per_100g = data["p"]
                updated = True
            if ingredient_obj.fat_per_100g is None:
                ingredient_obj.fat_per_100g = data["f"]
                updated = True
            if ingredient_obj.carbs_per_100g is None:
                ingredient_obj.carbs_per_100g = data["c"]
                updated = True
            if updated:
                ingredient_obj.save()

        rows.append(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_obj,
                grams=grams,
            )
        )

    if rows:
        RecipeIngredient.objects.bulk_create(rows)


def fetch_and_save_recipes(query="chicken"):
    encoded_query = quote(query.strip() or "chicken")
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={encoded_query}"

    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not fetch recipes from TheMealDB: %s", exc)
        return 0

    meals = payload.get("meals") or []
    saved = 0
    for meal in meals:
        api_id = str(meal.get("idMeal") or "").strip()
        if not api_id:
            continue

        ingredients = get_ingredients(meal)
        nutrition = calculate_nutrition(ingredients)

        with transaction.atomic():
            recipe, _ = Recipe.objects.update_or_create(
                api_id=api_id,
                defaults={
                    "name": (meal.get("strMeal") or "").strip(),
                    "category": (meal.get("strCategory") or "").strip() or None,
                    "instructions": (meal.get("strInstructions") or "").strip(),
                    "image_url": (meal.get("strMealThumb") or "").strip() or None,
                    "calories": float(nutrition["kcal"]),
                    "protein": float(nutrition["p"]),
                    "fat": float(nutrition["f"]),
                    "carbs": float(nutrition["c"]),
                },
            )
            _save_recipe_ingredients(recipe, ingredients)

        saved += 1
    return saved
