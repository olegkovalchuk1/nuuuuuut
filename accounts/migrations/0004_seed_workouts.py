from django.db import migrations


def seed_workouts(apps, schema_editor):
    Workout = apps.get_model("accounts", "Workout")

    workouts = [
        {
            "name": "Jump Rope Intervals",
            "description": "Alternating 60 seconds of fast jump rope with 30 seconds of light bouncing for cardiovascular endurance.",
            "category": "cardio",
            "duration_minutes": 20,
            "difficulty_level": "intermediate",
            "media_url": "https://www.youtube.com/watch?v=1BZM6Q9MFlM",
        },
        {
            "name": "HIIT Bodyweight Circuit",
            "description": "A high-intensity sequence of burpees, mountain climbers, and squat jumps to boost heart rate and calorie burn.",
            "category": "cardio",
            "duration_minutes": 18,
            "difficulty_level": "advanced",
            "media_url": "https://www.youtube.com/watch?v=ml6cT4AZdqI",
        },
        {
            "name": "Brisk Walking Session",
            "description": "Low-impact brisk walking aimed at improving aerobic health and supporting daily activity goals.",
            "category": "cardio",
            "duration_minutes": 30,
            "difficulty_level": "beginner",
            "media_url": "https://www.youtube.com/watch?v=njeZ29umqVE",
        },
        {
            "name": "Dumbbell Full-Body Strength",
            "description": "Compound strength workout including goblet squats, bent-over rows, and overhead presses.",
            "category": "strength",
            "duration_minutes": 35,
            "difficulty_level": "intermediate",
            "media_url": "https://www.youtube.com/watch?v=U0bhE67HuDY",
        },
        {
            "name": "Push-Up and Core Builder",
            "description": "Upper body and core focused routine with push-ups, plank holds, and dead bug variations.",
            "category": "strength",
            "duration_minutes": 25,
            "difficulty_level": "beginner",
            "media_url": "https://www.youtube.com/watch?v=IODxDxX7oi4",
        },
        {
            "name": "Lower Body Power Session",
            "description": "Strength-focused leg training with lunges, Romanian deadlifts, and glute bridge progressions.",
            "category": "strength",
            "duration_minutes": 32,
            "difficulty_level": "advanced",
            "media_url": "https://www.youtube.com/watch?v=2SHsk9AzdjA",
        },
        {
            "name": "Morning Mobility Flow",
            "description": "Gentle full-body stretching flow to improve mobility in hips, shoulders, and spine.",
            "category": "stretching",
            "duration_minutes": 15,
            "difficulty_level": "beginner",
            "media_url": "https://www.youtube.com/watch?v=v7AYKMP6rOE",
        },
        {
            "name": "Post-Workout Cooldown Stretch",
            "description": "Static stretches for hamstrings, quadriceps, calves, chest, and back to aid recovery.",
            "category": "stretching",
            "duration_minutes": 12,
            "difficulty_level": "beginner",
            "media_url": "https://www.youtube.com/watch?v=FSSDLDhbacc",
        },
        {
            "name": "Deep Stretch Yoga Session",
            "description": "Long-hold stretching poses inspired by yoga for flexibility and stress reduction.",
            "category": "stretching",
            "duration_minutes": 28,
            "difficulty_level": "intermediate",
            "media_url": "https://www.youtube.com/watch?v=4pKly2JojMw",
        },
    ]

    for workout in workouts:
        Workout.objects.update_or_create(
            name=workout["name"],
            defaults=workout,
        )


def unseed_workouts(apps, schema_editor):
    Workout = apps.get_model("accounts", "Workout")
    names = [
        "Jump Rope Intervals",
        "HIIT Bodyweight Circuit",
        "Brisk Walking Session",
        "Dumbbell Full-Body Strength",
        "Push-Up and Core Builder",
        "Lower Body Power Session",
        "Morning Mobility Flow",
        "Post-Workout Cooldown Stretch",
        "Deep Stretch Yoga Session",
    ]
    Workout.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_workout"),
    ]

    operations = [
        migrations.RunPython(seed_workouts, unseed_workouts),
    ]
