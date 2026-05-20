from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.html import format_html

from .models import CustomUser, Profile, Recipe, Workout


def _get_optional_model(model_name):
    try:
        return apps.get_model("accounts", model_name)
    except LookupError:
        return None


def _has_field(model, field_name):
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False


def _first_existing_field(model, *field_names):
    for field_name in field_names:
        if _has_field(model, field_name):
            return field_name
    return None


def _fk_names(model):
    return tuple(
        field.name
        for field in model._meta.get_fields()
        if isinstance(field, models.ForeignKey)
    )


def _fk_name_to_model(model, related_model):
    for field in model._meta.get_fields():
        if (
            isinstance(field, models.ForeignKey)
            and field.remote_field
            and field.remote_field.model is related_model
        ):
            return field.name
    return None


class OptimizedAdminMixin:
    list_per_page = 20
    show_full_result_count = False

    def get_raw_id_fields(self, request):
        return _fk_names(self.model)


class ThumbnailPreviewMixin:
    THUMBNAIL_CANDIDATES = (
        "image",
        "photo",
        "picture",
        "thumbnail",
        "media",
        "image_url",
        "media_url",
    )

    @admin.display(description="Preview")
    def thumbnail_preview(self, obj):
        for field_name in self.THUMBNAIL_CANDIDATES:
            if not hasattr(obj, field_name):
                continue
            value = getattr(obj, field_name)
            if not value:
                continue
            url = value.url if hasattr(value, "url") else str(value)
            return format_html(
                '<img src="{}" style="height:40px;width:40px;object-fit:cover;border-radius:6px;" />',
                url,
            )
        return "-"


Ingredient = _get_optional_model("Ingredient")
MealPlan = _get_optional_model("MealPlan")
ExerciseCategory = _get_optional_model("ExerciseCategory")
UserProfile = _get_optional_model("UserProfile")

RecipeNameField = _first_existing_field(Recipe, "title", "name", "name_recipe")
WorkoutTitleField = _first_existing_field(Workout, "title", "name")
WorkoutDescriptionField = _first_existing_field(Workout, "description", "details")
WorkoutDurationField = _first_existing_field(Workout, "duration", "duration_minutes")
WorkoutDifficultyField = _first_existing_field(Workout, "difficulty", "difficulty_level")
WorkoutCategoryField = _first_existing_field(Workout, "category", "exercise_category")
RecipeMealTypeField = _first_existing_field(
    Recipe,
    "meal_type",
    "meal_category",
    "meal_time",
    "goal_type",
)


if Ingredient:
    IngredientNameField = _first_existing_field(Ingredient, "name", "title")
    IngredientRecipeFK = _fk_name_to_model(Ingredient, Recipe)
else:
    IngredientNameField = None
    IngredientRecipeFK = None


if Ingredient and IngredientRecipeFK:
    class IngredientInline(OptimizedAdminMixin, admin.TabularInline):
        model = Ingredient
        fk_name = IngredientRecipeFK
        extra = 1

        if IngredientNameField and _has_field(Ingredient, "quantity"):
            fields = tuple(
                field_name
                for field_name in (
                    IngredientNameField,
                    "quantity",
                    "unit",
                    "calories",
                    "protein",
                    "fat",
                    "carbs",
                )
                if _has_field(Ingredient, field_name)
            )
        else:
            fields = tuple(
                field.name
                for field in Ingredient._meta.fields
                if field.name not in ("id", IngredientRecipeFK)
            )
else:
    IngredientInline = None


@admin.register(CustomUser)
class CustomUserAdmin(OptimizedAdminMixin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("age", "gender")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional info", {"fields": ("age", "gender")}),
    )
    list_display = ("id", "username", "email", "is_staff", "age", "gender")
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(Profile)
class UserProfileAdmin(OptimizedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "current_weight",
        "target_weight",
        "selected_goal",
        "activity_level",
        "date",
    )
    list_filter = tuple(
        field_name
        for field_name in ("goal", "activity_level")
        if _has_field(Profile, field_name)
    )
    search_fields = ("user__username", "user__email", "goal")
    ordering = ("user__username",)

    @admin.display(ordering="user__username", description="Username")
    def username(self, obj):
        return obj.user.username

    @admin.display(ordering="weight", description="Current Weight")
    def current_weight(self, obj):
        if _has_field(Profile, "current_weight"):
            return obj.current_weight
        return obj.weight if _has_field(Profile, "weight") else "-"

    @admin.display(description="Target Weight")
    def target_weight(self, obj):
        if _has_field(Profile, "target_weight"):
            return obj.target_weight
        return "-"

    @admin.display(ordering="goal", description="Goal")
    def selected_goal(self, obj):
        if _has_field(Profile, "goal"):
            return obj.get_goal_display() if hasattr(obj, "get_goal_display") else obj.goal
        return "-"


@admin.register(Recipe)
class RecipeAdmin(ThumbnailPreviewMixin, OptimizedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        RecipeNameField,
        "calories",
        "protein",
        "fats",
        "carbohydrates",
        "thumbnail_preview",
    )
    list_filter = tuple(
        field_name
        for field_name in (RecipeMealTypeField,)
        if field_name
    )
    ordering = (RecipeNameField,)
    inlines = [IngredientInline] if IngredientInline else []

    def get_search_fields(self, request):
        fields = [RecipeNameField]
        if Ingredient and IngredientNameField and IngredientRecipeFK:
            reverse_query_name = Ingredient._meta.model_name
            fields.append(f"{reverse_query_name}__{IngredientNameField}")
        return tuple(fields)

    @admin.display(ordering="fat", description="Fats")
    def fats(self, obj):
        if _has_field(Recipe, "fats"):
            return obj.fats
        return obj.fat if _has_field(Recipe, "fat") else "-"

    @admin.display(ordering="carbs", description="Carbohydrates")
    def carbohydrates(self, obj):
        if _has_field(Recipe, "carbohydrates"):
            return obj.carbohydrates
        return obj.carbs if _has_field(Recipe, "carbs") else "-"


@admin.register(Workout)
class WorkoutAdmin(ThumbnailPreviewMixin, OptimizedAdminMixin, admin.ModelAdmin):
    list_display = (
        "id",
        WorkoutTitleField,
        WorkoutCategoryField,
        WorkoutDurationField,
        WorkoutDifficultyField,
        "thumbnail_preview",
    )
    list_filter = tuple(
        field_name
        for field_name in (WorkoutCategoryField, WorkoutDifficultyField)
        if field_name
    )
    search_fields = tuple(
        field_name
        for field_name in (WorkoutTitleField, WorkoutDescriptionField)
        if field_name
    )
    ordering = (WorkoutTitleField,)
    list_editable = tuple(
        field_name
        for field_name in (WorkoutDurationField, WorkoutDifficultyField)
        if field_name and field_name != WorkoutTitleField
    )
    readonly_fields = tuple(
        field_name
        for field_name in ("created_at", "updated_at")
        if _has_field(Workout, field_name)
    )
    fieldsets = (
        (
            "Exercise Content",
            {
                "fields": tuple(
                    field_name
                    for field_name in (
                        WorkoutTitleField,
                        WorkoutCategoryField,
                        WorkoutDescriptionField,
                    )
                    if field_name
                ),
            },
        ),
        (
            "Technical Meta-data",
            {
                "fields": tuple(
                    field_name
                    for field_name in (
                        WorkoutDurationField,
                        WorkoutDifficultyField,
                        _first_existing_field(Workout, "image", "media_url"),
                        "created_at",
                        "updated_at",
                    )
                    if field_name and _has_field(Workout, field_name)
                ),
                "classes": ("collapse",),
            },
        ),
    )


if ExerciseCategory:
    @admin.register(ExerciseCategory)
    class ExerciseCategoryAdmin(OptimizedAdminMixin, admin.ModelAdmin):
        title_field = _first_existing_field(ExerciseCategory, "title", "name")
        list_display = tuple(
            field_name
            for field_name in (
                "id",
                title_field,
                _first_existing_field(ExerciseCategory, "slug", "code"),
            )
            if field_name
        )
        search_fields = (title_field,) if title_field else ()
        ordering = (title_field,) if title_field else ("id",)


if MealPlan:
    @admin.register(MealPlan)
    class MealPlanAdmin(ThumbnailPreviewMixin, OptimizedAdminMixin, admin.ModelAdmin):
        title_field = _first_existing_field(MealPlan, "title", "name")
        date_field = _first_existing_field(MealPlan, "date", "day", "scheduled_for")
        goal_field = _first_existing_field(MealPlan, "goal", "goal_type")

        list_display = tuple(
            field_name
            for field_name in (
                "id",
                title_field,
                _first_existing_field(MealPlan, "user", "profile"),
                date_field,
                goal_field,
                "thumbnail_preview",
            )
            if field_name
        )
        list_filter = tuple(
            field_name
            for field_name in (goal_field, date_field)
            if field_name
        )
        search_fields = tuple(
            field_name
            for field_name in (
                title_field,
                "user__username" if _has_field(MealPlan, "user") else None,
            )
            if field_name
        )
        ordering = tuple(field_name for field_name in (date_field, "id") if field_name)


if UserProfile and UserProfile is not Profile:
    @admin.register(UserProfile)
    class ExternalUserProfileAdmin(OptimizedAdminMixin, admin.ModelAdmin):
        list_display = tuple(
            field_name
            for field_name in (
                "id",
                _first_existing_field(UserProfile, "user", "username"),
                _first_existing_field(UserProfile, "current_weight", "weight"),
                _first_existing_field(UserProfile, "target_weight", "goal_weight"),
                _first_existing_field(UserProfile, "goal", "fitness_goal"),
                _first_existing_field(UserProfile, "activity_level", "activity"),
            )
            if field_name
        )
        list_filter = tuple(
            field_name
            for field_name in (
                _first_existing_field(UserProfile, "goal", "fitness_goal"),
                _first_existing_field(UserProfile, "activity_level", "activity"),
            )
            if field_name
        )
