from users.models import FoodEntry


def add_food(user, meal_type, food_name, calories): 
   # Додає продукт до певного прийому їжі
   
    return FoodEntry.objects.create(
        user=user,
        meal_type=meal_type,
        food_name=food_name,
        calories=calories
    )


def get_meal_calories(user, meal_type):
    # Повертає суму калорій для конкретного прийому їжі
  
    foods = FoodEntry.objects.filter(user=user, meal_type=meal_type)
    return sum(food.calories for food in foods)


def get_daily_calories(user):
    # Повертає загальну кількість калорій за день
    
    foods = FoodEntry.objects.filter(user=user)
    return sum(food.calories for food in foods)


def get_meal_details(user):
   # Повертає калорії по кожному прийому їжі
  
    return {
        "breakfast": get_meal_calories(user, "breakfast"),
        "lunch": get_meal_calories(user, "lunch"),
        "dinner": get_meal_calories(user, "dinner"),
    }

def delete_food(food_id):
    FoodEntry.objects.filter(id=food_id).delete()