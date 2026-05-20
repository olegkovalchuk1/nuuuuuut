from django.shortcuts import render

from django.shortcuts import render, redirect
from .nutrition import add_food

def add_food_view(request):
    if request.method == "POST":
        meal_type = request.POST.get("meal_type")
        food_name = request.POST.get("food_name")
        calories = float(request.POST.get("calories"))

        add_food(request.user, meal_type, food_name, calories)
        return redirect("home")  # куди хочеш після додавання

    return render(request, "add_food.html")