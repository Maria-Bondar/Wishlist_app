from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, UserProfile, Interest

class RegisterForm(UserCreationForm):
    """
    Form for registering a new user.
    Includes email (unique) and optional date of birth.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'})
    )
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'date_of_birth', 'password1', 'password2']


class EmailLoginForm(AuthenticationForm):
    """
    Form for logging in using email instead of username.
    """
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={'autofocus': True}))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput)
    

class UserProfileForm(forms.ModelForm):
    """
    Form for creating or editing a user's profile.
    Handles bio, profile picture, and social media handles.
    """
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic', 'facebook', 'twitter', 'instagram']
        
class EditUserForm(forms.ModelForm):
    """
    Form for editing a user's personal information, currently only date_of_birth.
    """
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    class Meta:
        model = CustomUser
        fields = ['date_of_birth']

        