from django import forms
from .models import ReturnNote
from .models import Asset
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class ReturnNoteForm(forms.ModelForm):

    class Meta:
        model = ReturnNote
        fields = ['asset', 'remarks', 'condition']


class AssetForm(forms.ModelForm):

    class Meta:
        model = Asset
        fields = '__all__'  # or list fields you want on the form


class CustomPasswordChangeForm(forms.Form):
    username = forms.CharField()
    current_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        user = authenticate(username=username, password=current_password)
        if not user:
            raise forms.ValidationError(
                "Invalid username or current password.")

        if new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")

        cleaned_data["user"] = user  # Save user for view
        return cleaned_data
