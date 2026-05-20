
def calculate_bmr(weight, height, age, gender):
    # 1 - чоловік, 0 - жінка
    if gender == 1:
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161


def calculate_tdee(bmr, activity_level):
    activity_coefficients = {
        "low": 1.2,
        "light": 1.375,
        "medium": 1.55,
        "high": 1.725,
    }

    return bmr * activity_coefficients.get(activity_level, 1.2)


def adjust_calories_for_goal(tdee, goal):
    if goal == "lose":
        return tdee * 0.85  
    elif goal == "gain":
        return tdee * 1.15  
    else:  
        return tdee


def calculate_user_calories(user):
    profile = user.profile

    bmr = calculate_bmr(
        weight=profile.weight,
        height=profile.height,
        age=profile.age,
        gender=profile.gender,
    )

    tdee = calculate_tdee(bmr, profile.activity_level)

    final_calories = adjust_calories_for_goal(tdee, profile.goal)

    return round(final_calories, 2)


    def calculate_water_intake(weight):
    return round((weight * 35) / 1000, 2)

    def calculate_user_water(user):
    profile = user.profile
    return calculate_water_intake(profile.weight)

