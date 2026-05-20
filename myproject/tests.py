from django.test import TestCase
from django.contrib.auth import get_user_model
from users.models import FoodEntry
from nutrition import add_food, get_meal_calories, get_daily_calories, get_meal_details, delete_food

User = get_user_model()

class NutritionTestCase(TestCase):
    
    def setUp(self):
        # Ініціалізація вашого кастомного тестового користувача
        self.user = User.objects.create_user(username='testuser', password='password')

    # ----------------------------------------------------------------------
    # БЛОК 1: Додавання даних
    # ----------------------------------------------------------------------
    
    def test_add_food(self):
        entry = add_food(self.user, "breakfast", "Apple", 50)
        self.assertEqual(FoodEntry.objects.count(), 1)
        self.assertEqual(entry.food_name, "Apple")

    # ----------------------------------------------------------------------
    # БЛОК 2: Розрахунки калорій
    # ----------------------------------------------------------------------
    
    def test_get_meal_calories(self):
        add_food(self.user, "lunch", "Soup", 200)
        add_food(self.user, "lunch", "Bread", 100)
        self.assertEqual(get_meal_calories(self.user, "lunch"), 300)

    def test_get_daily_calories(self):
        add_food(self.user, "breakfast", "Egg", 100)
        add_food(self.user, "dinner", "Salad", 150)
        self.assertEqual(get_daily_calories(self.user), 250)

    # ----------------------------------------------------------------------
    # БЛОК 3: Форматування та агрегація
    # ----------------------------------------------------------------------

    def test_get_meal_details(self):
        add_food(self.user, "breakfast", "Coffee", 10)
        details = get_meal_details(self.user)
        self.assertEqual(details["breakfast"], 10)
        self.assertEqual(details["lunch"], 0)
        self.assertEqual(details["dinner"], 0)

    # ----------------------------------------------------------------------
    # БЛОК 4: Видалення даних
    # ----------------------------------------------------------------------

    def test_delete_food(self):
        food = add_food(self.user, "dinner", "Fish", 300)
        self.assertEqual(FoodEntry.objects.count(), 1)
        
        delete_food(food.id)
        self.assertEqual(FoodEntry.objects.count(), 0)