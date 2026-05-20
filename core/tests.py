from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import KcalTracker, UserProfile, WaterTracker, Workout, WorkoutTracker


class WorkoutSectionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="testpass123",
        )
        self.workout = Workout.objects.create(
            workout_type="Cardio",
            duration=30,
        )

    def test_workout_list_requires_authentication(self):
        response = self.client.get(reverse("workout_list"))
        self.assertEqual(response.status_code, 302)

    def test_user_can_mark_workout_as_done(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("mark_workout_done", args=[self.workout.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            WorkoutTracker.objects.filter(
                user=self.user,
                workout=self.workout,
                date=timezone.localdate(),
            ).exists()
        )

    def test_mark_workout_as_done_is_idempotent_for_same_day(self):
        self.client.login(username="testuser", password="testpass123")
        url = reverse("mark_workout_done", args=[self.workout.id])

        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            WorkoutTracker.objects.filter(
                user=self.user,
                workout=self.workout,
                date=timezone.localdate(),
            ).count(),
            1,
        )


class StatsApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stats-user",
            password="testpass123",
        )
        self.client.login(username="stats-user", password="testpass123")
        UserProfile.objects.create(
            user=self.user,
            age=30,
            gender="M",
            weight=82,
            height=181,
            activity_level="medium",
            daily_calorie_limit=2200,
        )

    def test_calories_stats_returns_consumption_and_limit_lines(self):
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        first = KcalTracker.objects.create(
            user=self.user,
            calories=1800,
            protein=120,
            fat=60,
            carbs=180,
        )
        KcalTracker.objects.filter(pk=first.pk).update(date=yesterday)
        KcalTracker.objects.create(
            user=self.user,
            calories=2100,
            protein=150,
            fat=70,
            carbs=200,
        )

        response = self.client.get(reverse("calories_stats_api"), {"period": "week"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(len(payload["labels"]), 7)
        consumed = payload["datasets"][0]["data"]
        limit = payload["datasets"][1]["data"]

        yesterday_index = payload["labels"].index(yesterday.isoformat())
        today_index = payload["labels"].index(today.isoformat())

        self.assertEqual(consumed[yesterday_index], 1800)
        self.assertEqual(consumed[today_index], 2100)
        self.assertTrue(all(value == 2200 for value in limit))

    def test_macros_today_returns_bju_totals(self):
        KcalTracker.objects.create(
            user=self.user,
            calories=2000,
            protein=130,
            fat=65,
            carbs=210,
        )

        response = self.client.get(reverse("macros_today_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["datasets"][0]["data"], [130.0, 65.0, 210.0])
        self.assertAlmostEqual(payload["percentages"]["protein"], 32.1, places=1)

    def test_workouts_week_stats_groups_burned_calories_by_weekday(self):
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        wednesday = week_start + timedelta(days=2)

        cardio = Workout.objects.create(
            workout_type="Cardio",
            duration=30,
            calories_burned=300,
        )
        strength = Workout.objects.create(
            workout_type="Strength",
            duration=40,
            calories_burned=200,
        )

        tracker_1 = WorkoutTracker.objects.create(user=self.user, workout=cardio)
        WorkoutTracker.objects.filter(pk=tracker_1.pk).update(date=week_start)
        tracker_2 = WorkoutTracker.objects.create(user=self.user, workout=strength)
        WorkoutTracker.objects.filter(pk=tracker_2.pk).update(date=wednesday)

        response = self.client.get(reverse("workouts_week_stats_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["datasets"][0]["data"][0], 300)  # Monday
        self.assertEqual(payload["datasets"][0]["data"][2], 200)  # Wednesday

    def test_water_week_stats_groups_intake_by_weekday(self):
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        friday = week_start + timedelta(days=4)

        first = WaterTracker.objects.create(user=self.user, amount=1800)
        WaterTracker.objects.filter(pk=first.pk).update(date=week_start)
        second = WaterTracker.objects.create(user=self.user, amount=2300)
        WaterTracker.objects.filter(pk=second.pk).update(date=friday)

        response = self.client.get(reverse("water_week_stats_api"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["datasets"][0]["data"][0], 1800)  # Monday
        self.assertEqual(payload["datasets"][0]["data"][4], 2300)  # Friday
