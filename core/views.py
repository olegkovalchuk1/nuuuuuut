import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from recipes.models import Recipe as ExternalRecipe

from .models import (
    KcalTracker,
    Notification,
    Recipe as CoreRecipe,
    UserProfile,
    WaterTracker,
    Workout,
    WorkoutTracker,
)


def _date_range(start_date, days_count):
    return [start_date + timedelta(days=index) for index in range(days_count)]


def _wants_json(request):
    accept = request.headers.get("Accept", "")
    return request.GET.get("format") == "json" or "application/json" in accept


def _parse_json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _serialize_notification(item):
    return {
        "id": item.id,
        "text": item.text,
        "important": item.important,
        "read": item.read,
        "source_key": item.source_key,
        "created_at": item.created_at.isoformat(),
    }


def _json_or_fallback(response, fallback):
    if getattr(response, "status_code", 500) != 200:
        return fallback
    try:
        return json.loads(response.content.decode("utf-8"))
    except (TypeError, ValueError, UnicodeDecodeError):
        return fallback


def _staff_api_guard(request):
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required."}, status=401)
    if not request.user.is_staff:
        return JsonResponse({"detail": "Staff access required."}, status=403)
    return None


def _staff_page_guard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Staff access required.")
    return None


def login_page(request):
    return render(request, "login.html")


def signup_page(request):
    return render(request, "signup.html")


@login_required
def profile_page(request):
    return render(request, "profile.html")


@login_required
def notifications_page(request):
    return render(request, "notifications.html")


@login_required
def test_page(request):
    return render(request, "test.html")


@login_required
def exercise_page(request):
    return render(request, "exercise.html")


@login_required
def recipes_page(request):
    return render(request, "recipes.html")


@login_required
def admin_panel_page(request):
    blocked = _staff_page_guard(request)
    if blocked:
        return blocked
    return render(request, "admin.html")


@login_required
def admin_users_page(request):
    blocked = _staff_page_guard(request)
    if blocked:
        return blocked
    return render(request, "admin-users.html")


@login_required
def admin_foods_page(request):
    blocked = _staff_page_guard(request)
    if blocked:
        return blocked
    return render(request, "admin-foods.html")


@login_required
def admin_analytics_page(request):
    blocked = _staff_page_guard(request)
    if blocked:
        return blocked
    return render(request, "admin-analytics.html")


@login_required
def workout_list(request):
    category = request.GET.get("category")
    difficulty = request.GET.get("difficulty")
    search_query = request.GET.get("q")

    workouts = Workout.objects.all()

    if category:
        workouts = workouts.filter(category__iexact=category)
    if difficulty:
        workouts = workouts.filter(difficulty_level__iexact=difficulty)
    if search_query:
        workouts = workouts.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    workouts = workouts.order_by("category", "name")

    date_str = request.GET.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    completed_workout_ids = set(
        WorkoutTracker.objects.filter(user=request.user, date=target_date).values_list(
            "workout_id", flat=True
        )
    )

    if _wants_json(request):
        year = _to_int(request.GET.get("year"), target_date.year)
        month = _to_int(request.GET.get("month"), target_date.month)

        try:
            month_start = datetime(year, month, 1).date()
        except (ValueError, TypeError):
            month_start = target_date.replace(day=1)

        if month_start.month == 12:
            next_month = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month = month_start.replace(month=month_start.month + 1)

        completed_dates = list(
            WorkoutTracker.objects.filter(
                user=request.user,
                date__gte=month_start,
                date__lt=next_month,
            )
            .values_list("date", flat=True)
            .distinct()
            .order_by("date")
        )
        return JsonResponse(
            {
                "today": timezone.localdate().isoformat(),
                "target_date": target_date.isoformat(),
                "completed_workout_ids": sorted(completed_workout_ids),
                "completed_dates": [day.isoformat() for day in completed_dates],
                "workouts": [
                    {
                        "id": item.id,
                        "name": item.name,
                        "duration": item.duration_minutes,
                        "calories_burned": item.calories_burned,
                        "link": item.media_url,
                        "description": item.description,
                        "category": item.category,
                        "difficulty": item.difficulty_level,
                        "completed_today": item.id in completed_workout_ids,
                    }
                    for item in workouts
                ],
            }
        )

    return render(
        request,
        "workouts/list.html",
        {
            "workouts": workouts,
            "completed_workout_ids": completed_workout_ids,
            "today": target_date,
        },
    )


@login_required
@require_POST
def mark_workout_done(request, workout_id):
    workout = get_object_or_404(Workout, pk=workout_id)
    payload = _parse_json_body(request)

    date_str = payload.get("date")
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = timezone.localdate()
    else:
        target_date = timezone.localdate()

    done = _to_bool(payload.get("done"), default=True)

    tracker_qs = WorkoutTracker.objects.filter(
        user=request.user,
        workout=workout,
        date=target_date,
    )
    if done:
        WorkoutTracker.objects.get_or_create(user=request.user, workout=workout, date=target_date)
    else:
        tracker_qs.delete()

    if _wants_json(request) or request.content_type == "application/json":
        return JsonResponse(
            {
                "status": "ok",
                "workout_id": workout.id,
                "done": done,
                "date": target_date.isoformat(),
            }
        )
    return redirect("workout_list")


@require_GET
@login_required
def calories_stats_api(request):
    period = request.GET.get("period", "week")
    days_map = {"week": 7, "month": 30}
    if period not in days_map:
        return JsonResponse({"error": "period must be 'week' or 'month'"}, status=400)

    days_count = days_map[period]
    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days_count - 1)

    rows = (
        KcalTracker.objects.filter(user=request.user, date__range=(start_date, end_date))
        .values("date")
        .annotate(
            total_calories=Coalesce(
                Sum("calories"),
                Value(0, output_field=IntegerField()),
            )
        )
        .order_by("date")
    )
    calories_by_date = {row["date"]: int(row["total_calories"]) for row in rows}

    labels = []
    calories_data = []
    for day in _date_range(start_date, days_count):
        labels.append(day.isoformat())
        calories_data.append(calories_by_date.get(day, 0))

    profile = UserProfile.objects.filter(user=request.user).only("daily_calorie_limit").first()
    daily_limit = profile.daily_calorie_limit if profile else 2000

    return JsonResponse(
        {
            "labels": labels,
            "datasets": [
                {
                    "label": "Calories eaten",
                    "data": calories_data,
                    "borderColor": "#1f77b4",
                    "backgroundColor": "rgba(31, 119, 180, 0.15)",
                    "fill": True,
                    "tension": 0.25,
                },
                {
                    "label": "Daily limit",
                    "data": [daily_limit] * len(labels),
                    "borderColor": "#d62728",
                    "borderDash": [8, 6],
                    "fill": False,
                    "tension": 0,
                },
            ],
        }
    )


@require_GET
@login_required
def dashboard_stats_api(request):
    period = request.GET.get("period", "week")
    if period not in {"week", "month"}:
        period = "week"

    calories_fallback = {
        "labels": [],
        "datasets": [
            {
                "label": "Calories eaten",
                "data": [],
                "borderColor": "#1f77b4",
                "backgroundColor": "rgba(31, 119, 180, 0.15)",
                "fill": True,
                "tension": 0.25,
            },
            {
                "label": "Daily limit",
                "data": [],
                "borderColor": "#d62728",
                "borderDash": [8, 6],
                "fill": False,
                "tension": 0,
            },
        ],
    }
    macros_fallback = {
        "labels": ["Protein", "Fat", "Carbs"],
        "datasets": [
            {
                "label": "Macros (g)",
                "data": [0, 0, 0],
                "backgroundColor": ["#2ca02c", "#ff7f0e", "#1f77b4"],
            }
        ],
        "percentages": {"protein": 0.0, "fat": 0.0, "carbs": 0.0},
        "date": timezone.localdate().isoformat(),
    }
    week_fallback = {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "datasets": [{"label": "Value", "data": [0, 0, 0, 0, 0, 0, 0]}],
        "week_start": timezone.localdate().isoformat(),
        "week_end": timezone.localdate().isoformat(),
    }

    mutable_get = request.GET.copy()
    mutable_get["period"] = period
    request.GET = mutable_get

    calories = _json_or_fallback(calories_stats_api(request), calories_fallback)
    macros = _json_or_fallback(macros_today_api(request), macros_fallback)
    workouts = _json_or_fallback(workouts_week_stats_api(request), week_fallback)
    water = _json_or_fallback(
        water_week_stats_api(request),
        {
            **week_fallback,
            "datasets": [
                {
                    "label": "Water intake (ml)",
                    "data": [0, 0, 0, 0, 0, 0, 0],
                    "borderColor": "#0ea5e9",
                    "backgroundColor": "rgba(14, 165, 233, 0.25)",
                    "fill": True,
                    "tension": 0.25,
                }
            ],
        },
    )

    return JsonResponse(
        {
            "period": period,
            "calories": calories,
            "macros": macros,
            "workouts": workouts,
            "water": water,
        }
    )


@require_GET
@login_required
def macros_today_api(request):
    today = timezone.localdate()

    totals = KcalTracker.objects.filter(user=request.user, date=today).aggregate(
        protein=Coalesce(Sum("protein"), Value(0.0)),
        fat=Coalesce(Sum("fat"), Value(0.0)),
        carbs=Coalesce(Sum("carbs"), Value(0.0)),
    )
    protein = float(totals["protein"])
    fat = float(totals["fat"])
    carbs = float(totals["carbs"])
    total = protein + fat + carbs

    def _percent(value):
        return round((value / total) * 100, 1) if total else 0.0

    return JsonResponse(
        {
            "labels": ["Protein", "Fat", "Carbs"],
            "datasets": [
                {
                    "label": "Macros (g)",
                    "data": [protein, fat, carbs],
                    "backgroundColor": ["#2ca02c", "#ff7f0e", "#1f77b4"],
                }
            ],
            "percentages": {
                "protein": _percent(protein),
                "fat": _percent(fat),
                "carbs": _percent(carbs),
            },
            "date": today.isoformat(),
        }
    )


@require_GET
@login_required
def workouts_week_stats_api(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    rows = (
        WorkoutTracker.objects.filter(user=request.user, date__range=(week_start, week_end))
        .values("date")
        .annotate(
            burned_calories=Coalesce(
                Sum("workout__calories_burned"),
                Value(0, output_field=IntegerField()),
            )
        )
        .order_by("date")
    )
    burned_by_date = {row["date"]: int(row["burned_calories"]) for row in rows}

    dates = _date_range(week_start, 7)
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    data = [burned_by_date.get(day, 0) for day in dates]

    return JsonResponse(
        {
            "labels": labels,
            "datasets": [
                {
                    "label": "Burned calories",
                    "data": data,
                    "backgroundColor": "#17a2b8",
                }
            ],
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }
    )


@require_GET
@login_required
def water_week_stats_api(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    rows = (
        WaterTracker.objects.filter(user=request.user, date__range=(week_start, week_end))
        .values("date")
        .annotate(
            total_amount=Coalesce(
                Sum("amount"),
                Value(0, output_field=IntegerField()),
            )
        )
        .order_by("date")
    )
    water_by_date = {row["date"]: int(row["total_amount"]) for row in rows}

    dates = _date_range(week_start, 7)
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    data = [water_by_date.get(day, 0) for day in dates]

    return JsonResponse(
        {
            "labels": labels,
            "datasets": [
                {
                    "label": "Water intake (ml)",
                    "data": data,
                    "borderColor": "#0ea5e9",
                    "backgroundColor": "rgba(14, 165, 233, 0.25)",
                    "fill": True,
                    "tension": 0.25,
                }
            ],
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def nutrition_today_api(request):
    today = timezone.localdate()

    if request.method == "GET":
        entry = KcalTracker.objects.filter(user=request.user, date=today).first()
        if not entry:
            return JsonResponse(
                {
                    "date": today.isoformat(),
                    "calories": 0,
                    "protein": 0,
                    "fat": 0,
                    "carbs": 0,
                }
            )
        return JsonResponse(
            {
                "date": today.isoformat(),
                "calories": int(entry.calories),
                "protein": float(entry.protein),
                "fat": float(entry.fat),
                "carbs": float(entry.carbs),
            }
        )

    payload = _parse_json_body(request)
    calories = max(0, _to_int(payload.get("calories"), 0))
    protein = max(0.0, _to_float(payload.get("protein"), 0.0))
    fat = max(0.0, _to_float(payload.get("fat"), 0.0))
    carbs = max(0.0, _to_float(payload.get("carbs"), 0.0))

    entry = KcalTracker.objects.filter(user=request.user, date=today).first()
    if entry:
        entry.calories = calories
        entry.protein = protein
        entry.fat = fat
        entry.carbs = carbs
        entry.save(update_fields=["calories", "protein", "fat", "carbs"])
    else:
        entry = KcalTracker.objects.create(
            user=request.user,
            calories=calories,
            protein=protein,
            fat=fat,
            carbs=carbs,
        )

    return JsonResponse(
        {
            "message": "Nutrition totals saved.",
            "date": today.isoformat(),
            "calories": int(entry.calories),
            "protein": float(entry.protein),
            "fat": float(entry.fat),
            "carbs": float(entry.carbs),
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def notifications_api(request):
    if request.method == "GET":
        scope = (request.GET.get("scope") or "all").strip().lower()
        queryset = Notification.objects.filter(user=request.user).order_by("-created_at")
        if scope == "important":
            queryset = queryset.filter(important=True)
        elif scope == "unread":
            queryset = queryset.filter(read=False)
        return JsonResponse({"results": [_serialize_notification(item) for item in queryset]})

    payload = _parse_json_body(request)
    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "text is required"}, status=400)

    important = _to_bool(payload.get("important"), default=False)
    source_key = (payload.get("source_key") or "").strip() or None

    if source_key:
        notification, created = Notification.objects.get_or_create(
            user=request.user,
            source_key=source_key,
            defaults={
                "text": text,
                "important": important,
                "read": False,
            },
        )
        if not created:
            return JsonResponse(
                {"notification": _serialize_notification(notification)},
                status=200,
            )
    else:
        notification = Notification.objects.create(
            user=request.user,
            text=text,
            important=important,
            read=False,
        )
        created = True

    return JsonResponse(
        {"notification": _serialize_notification(notification)},
        status=201 if created else 200,
    )


@login_required
@require_POST
def notification_mark_read_api(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    notification.read = True
    notification.save(update_fields=["read"])
    return JsonResponse({"status": "ok", "notification": _serialize_notification(notification)})


@require_GET
@login_required
def stats_dashboard(request):
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())

    mock_summary = {
        "weight_kg": 72.0,
        "calories_goal": 2200,
        "calories_today": 1850,
        "workouts_week": 3,
        "water_today_ml": 1800,
    }

    profile = (
        UserProfile.objects.filter(user=request.user).only("weight", "daily_calorie_limit").first()
    )
    weight_kg = round(profile.weight, 1) if profile else mock_summary["weight_kg"]
    calories_goal = profile.daily_calorie_limit if profile else mock_summary["calories_goal"]

    calories_today_qs = KcalTracker.objects.filter(user=request.user, date=today)
    calories_today = (
        int(calories_today_qs.aggregate(total=Coalesce(Sum("calories"), Value(0)))["total"])
        if calories_today_qs.exists()
        else mock_summary["calories_today"]
    )

    workouts_week_qs = WorkoutTracker.objects.filter(
        user=request.user,
        date__range=(week_start, today),
    )
    workouts_week = workouts_week_qs.count() if workouts_week_qs.exists() else mock_summary["workouts_week"]

    water_today_qs = WaterTracker.objects.filter(user=request.user, date=today)
    water_today_ml = (
        int(water_today_qs.aggregate(total=Coalesce(Sum("amount"), Value(0)))["total"])
        if water_today_qs.exists()
        else mock_summary["water_today_ml"]
    )

    context = {
        "dashboard_summary": {
            "weight_kg": weight_kg,
            "calories_goal": calories_goal,
            "calories_today": calories_today,
            "workouts_week": workouts_week,
            "water_today_ml": water_today_ml,
        },
        "api_endpoints": {
            "dashboard": reverse("dashboard_stats_api"),
            "calories": reverse("calories_stats_api"),
            "macros": reverse("macros_today_api"),
            "workouts": reverse("workouts_week_stats_api"),
            "water": reverse("water_week_stats_api"),
        },
    }
    return render(request, "stats/dashboard.html", context)


@require_GET
@login_required
def admin_users_api(request):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    User = get_user_model()
    users = User.objects.order_by("id")
    return JsonResponse(
        {
            "results": [
                {
                    "id": user.id,
                    "name": user.get_full_name() or user.username,
                    "email": user.email,
                    "blocked": not user.is_active,
                }
                for user in users
            ]
        }
    )


@login_required
@require_http_methods(["POST", "PATCH"])
def admin_user_block_api(request, user_id):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    if user.id == request.user.id:
        return JsonResponse({"error": "You cannot block yourself."}, status=400)

    payload = _parse_json_body(request)
    blocked = _to_bool(payload.get("blocked"), default=False)
    user.is_active = not blocked
    user.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "status": "ok",
            "id": user.id,
            "blocked": blocked,
        }
    )


@login_required
@require_http_methods(["GET", "POST"])
def admin_foods_api(request):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    if request.method == "GET":
        items = CoreRecipe.objects.order_by("id")
        return JsonResponse(
            {
                "results": [
                    {"id": item.id, "name": item.name, "val": int(item.calories)}
                    for item in items
                ]
            }
        )

    payload = _parse_json_body(request)
    name = (payload.get("name") or "").strip()
    val = _to_int(payload.get("val"), default=0)
    if not name:
        return JsonResponse({"error": "name is required"}, status=400)
    if val < 0:
        return JsonResponse({"error": "val must be >= 0"}, status=400)

    item = CoreRecipe.objects.create(
        name=name,
        description="",
        calories=val,
        protein=0,
        fat=0,
        carbs=0,
        goal_type="general",
        created_by=request.user,
    )
    return JsonResponse({"id": item.id, "name": item.name, "val": int(item.calories)}, status=201)


@login_required
@require_http_methods(["DELETE"])
def admin_food_delete_api(request, item_id):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    item = get_object_or_404(CoreRecipe, pk=item_id)
    item.delete()
    return JsonResponse({"status": "ok", "id": item_id})


@login_required
@require_http_methods(["GET", "POST"])
def admin_workouts_api(request):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    if request.method == "GET":
        items = Workout.objects.order_by("id")
        return JsonResponse(
            {
                "results": [
                    {"id": item.id, "name": item.name, "val": int(item.duration_minutes)}
                    for item in items
                ]
            }
        )

    payload = _parse_json_body(request)
    name = (payload.get("name") or "").strip()
    val = _to_int(payload.get("val"), default=0)
    if not name:
        return JsonResponse({"error": "name is required"}, status=400)
    if val < 1:
        return JsonResponse({"error": "val must be >= 1"}, status=400)

    item = Workout.objects.create(
        name=name,
        duration_minutes=val,
        calories_burned=max(0, val * 6),
        category=Workout.Category.STRENGTH,
        difficulty_level=Workout.Difficulty.BEGINNER,
        created_by=request.user,
    )
    return JsonResponse({"id": item.id, "name": item.name, "val": int(item.duration_minutes)}, status=201)


@login_required
@require_http_methods(["DELETE"])
def admin_workout_delete_api(request, item_id):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    item = get_object_or_404(Workout, pk=item_id)
    item.delete()
    return JsonResponse({"status": "ok", "id": item_id})


@require_GET
@login_required
def admin_analytics_api(request):
    guard = _staff_api_guard(request)
    if guard:
        return guard

    User = get_user_model()
    today = timezone.localdate()

    user_count = User.objects.count()
    food_count = CoreRecipe.objects.count() + ExternalRecipe.objects.count()
    workout_count = Workout.objects.count()

    recent_from = today - timedelta(days=30)
    active_users = (
        User.objects.filter(
            Q(workouttracker__date__gte=recent_from)
            | Q(kcaltracker__date__gte=recent_from)
            | Q(watertracker__date__gte=recent_from)
        )
        .distinct()
        .count()
    )
    activity_rate = f"{round((active_users / user_count) * 100) if user_count else 0}%"

    current_week_start = today - timedelta(days=today.weekday())
    prev_week_start = current_week_start - timedelta(days=7)
    prev_week_end = current_week_start - timedelta(days=1)

    current_week_actions = WorkoutTracker.objects.filter(
        date__range=(current_week_start, today)
    ).count()
    prev_week_actions = WorkoutTracker.objects.filter(
        date__range=(prev_week_start, prev_week_end)
    ).count()

    if prev_week_actions == 0:
        trend_value = 100 if current_week_actions else 0
    else:
        trend_value = round(
            ((current_week_actions - prev_week_actions) / prev_week_actions) * 100
        )

    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_dates = [current_week_start + timedelta(days=index) for index in range(7)]
    counts_by_day = {
        row["date"]: row["count"]
        for row in WorkoutTracker.objects.filter(
            date__range=(current_week_start, current_week_start + timedelta(days=6))
        )
        .values("date")
        .annotate(count=Count("id"))
    }
    week_activity = [counts_by_day.get(day, 0) for day in day_dates]

    return JsonResponse(
        {
            "userCount": user_count,
            "foodCount": food_count,
            "workoutCount": workout_count,
            "activityRate": activity_rate,
            "trend": f"{trend_value:+d}%",
            "weekLabels": labels,
            "weekActivity": week_activity,
        }
    )
