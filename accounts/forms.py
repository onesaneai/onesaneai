# accounts/forms.py
from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import pyotp

User = get_user_model()

class CustomAdminAuthenticationForm(AdminAuthenticationForm):
    username = forms.CharField(
        label=_("Username or Email"),
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': 'Username or Email'})
    )

    # Extra field for 2FA code
    totp_code = forms.CharField(
        label=_("2FA Code"),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter 2fa OTP',"otp":'none'})
    )

 