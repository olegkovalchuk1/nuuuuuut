from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Profile


User = get_user_model()


class SaveGoalViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="nutfit_user",
            email="nutfit@example.com",
            password="StrongPass123",
        )
        self.url = reverse("save-goal")
        self.client.force_authenticate(user=self.user)

    def test_create_profile_goal_data(self):
        payload = {
            "age": 29,
            "weight": 72.5,
            "height": 175.0,
            "activity_level": "moderate",
            "goal": Profile.GOAL_WEIGHT_LOSS,
            "date": "2026-03-26",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.age, payload["age"])
        self.assertEqual(profile.goal, payload["goal"])

    def test_update_existing_profile_goal_data(self):
        Profile.objects.create(
            user=self.user,
            age=30,
            weight=80.0,
            height=180.0,
            activity_level="low",
            goal=Profile.GOAL_MAINTENANCE,
            date="2026-03-25",
        )
        payload = {
            "age": 31,
            "weight": 78.0,
            "height": 180.0,
            "activity_level": "high",
            "goal": Profile.GOAL_WEIGHT_GAIN,
            "date": "2026-03-26",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.age, payload["age"])
        self.assertEqual(profile.weight, payload["weight"])
        self.assertEqual(profile.goal, payload["goal"])
        self.assertEqual(Profile.objects.filter(user=self.user).count(), 1)

    def test_reject_invalid_goal_choice(self):
        payload = {
            "age": 29,
            "weight": 72.5,
            "height": 175.0,
            "activity_level": "moderate",
            "goal": "invalid_goal",
            "date": "2026-03-26",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
