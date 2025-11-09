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
        widget=forms.TextInput(attrs={'placeholder': 'Enter 2FA Code (if enabled)'})
    )

    def confirm_login_allowed(self, user):
        """Called after user credentials are validated."""
        super().confirm_login_allowed(user)

        # Only enforce 2FA if user has enabled it
        if getattr(user, "is_2fa_enabled", False):
            totp_code = self.cleaned_data.get("totp_code")
            if not totp_code:
                raise forms.ValidationError(
                    _("Please enter your 2FA code."), code="missing_totp"
                )

            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(totp_code):
                raise forms.ValidationError(
                    _("Invalid 2FA code. Please try again."), code="invalid_totp"
                )
