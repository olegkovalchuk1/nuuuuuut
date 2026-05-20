from django.db import models


class Recipe(models.Model):
    api_id = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=120, null=True, blank=True)
    instructions = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    calories = models.FloatField(null=True, blank=True)
    protein = models.FloatField(null=True, blank=True)
    fat = models.FloatField(null=True, blank=True)
    carbs = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=180, unique=True)
    calories_per_100g = models.FloatField(null=True, blank=True)
    protein_per_100g = models.FloatField(null=True, blank=True)
    fat_per_100g = models.FloatField(null=True, blank=True)
    carbs_per_100g = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients",
    )
    grams = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="uniq_recipe_ingredient",
            )
        ]
