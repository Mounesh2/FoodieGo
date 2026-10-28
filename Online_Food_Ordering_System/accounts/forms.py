from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile

class NewUSerForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=False, initial='9876543210')
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), initial='Bengaluru, Karnataka')

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data.get("phone_number", "")
            profile.address = self.cleaned_data.get("address", "")
            profile.save()
        return user