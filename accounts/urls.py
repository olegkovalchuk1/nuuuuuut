from django.urls import path

from .views import (
    LoginView,
    LogoutView,
    RecipeListView,
    RegisterView,
    SaveGoalView,
    WorkoutListView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("goal/", SaveGoalView.as_view(), name="save-goal"),
    path("recipes/", RecipeListView.as_view(), name="recipe-list"),
    path("workouts/", WorkoutListView.as_view(), name="workout-list"),
]
