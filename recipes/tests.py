from django.test import SimpleTestCase

from recipes.services.recipe_service import calculate_calories, parse_ingredient


class RecipeServiceSimpleTests(SimpleTestCase):
    def test_parse_ingredient_cup(self):
        parsed = parse_ingredient("1 cup rice")
        self.assertEqual(parsed["ingredient"], "rice")
        self.assertAlmostEqual(parsed["grams"], 240.0, delta=1)

    def test_parse_ingredient_tbsp(self):
        parsed = parse_ingredient("2 tbsp sugar")
        self.assertEqual(parsed["ingredient"], "sugar")
        self.assertAlmostEqual(parsed["grams"], 30.0, delta=1)

    def test_parse_ingredient_pinch(self):
        parsed = parse_ingredient("pinch salt")
        self.assertEqual(parsed["ingredient"], "salt")
        self.assertAlmostEqual(parsed["grams"], 1.0, delta=0.1)

    def test_parse_ingredient_tsp(self):
        parsed = parse_ingredient("3 tsp honey")
        self.assertEqual(parsed["ingredient"], "honey")
        self.assertAlmostEqual(parsed["grams"], 15.0, delta=1)

    def test_parse_ingredient_slice(self):
        parsed = parse_ingredient("2 slices bread")
        self.assertEqual(parsed["ingredient"], "bread")
        self.assertAlmostEqual(parsed["grams"], 50.0, delta=1)

    def test_calculate_calories_uses_default_when_unknown(self):
        ingredients = [
            {"ingredient": "rice", "grams": 240},
            {"ingredient": "unknown product", "grams": 50},
        ]
        # rice: 240 * 130 / 100 = 312; unknown: 50 * 100 / 100 = 50
        self.assertEqual(calculate_calories(ingredients), 362)
