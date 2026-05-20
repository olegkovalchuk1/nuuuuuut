from django import forms

from .models import Profile


class ProfileGoalForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("age", "weight", "height", "activity_level", "goal", "date")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.Meta.fields:
            self.fields[field_name].required = True
