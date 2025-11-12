from django.contrib import admin
from .models import Profile,Contact,APIKey
# Register your models here.
# users/admin.py

import base64
import qrcode
from io import BytesIO
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils.html import format_html
import qrcode
import qrcode.image.svg
from io import BytesIO

from .forms import CustomAdminAuthenticationForm

# Override the default admin login view to use our form
admin.site.login_form = CustomAdminAuthenticationForm

# ========================== Update admin pannel  ====================================================
# onesaneai/admin.py or yourapp/admin.py
admin.site.site_header = "Onesane Admin Panel"
admin.site.site_title = "Onesane Admin"
admin.site.index_title = "Welcome to the Onesane Admin Panel"


# Profile model admin
@admin.register(Profile)
class ProfileAdmin(BaseUserAdmin):
    model = Profile
    ordering = ['email']
    list_display = ['email', 'username', 'is_staff', 'is_active', 'is_2fa_enabled', 'AuthCode']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']
    readonly_fields = ['totp_secret','show_totp_qr']

    fieldsets = (
        (_('Login Info'), {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('username', 'first_name', 'last_name','date_of_birth','city','country', 'profile_image')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified','groups', 'user_permissions')
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('Auth Verification'), {
            'fields': ('is_2fa_enabled','totp_secret','show_totp_qr',)
        }),

    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    search_fields = ['email', 'username']


    def AuthCode(self,obj):
        if obj.is_2fa_enabled and obj.totp_secret:
            return format_html(f'<a style="border: 1px solid orange;padding: 6px;border-radius: 6px;background: orange;color: white;"  href="/admin/accounts/profile/{obj.id}/change/#auth-verification-tab">Show QR Code</a>')
        return "2FA not enabled"

    def show_totp_qr(self, obj):
        if obj.is_2fa_enabled and obj.totp_secret:
            qr = qrcode.make(obj.get_totp_uri())
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            html = f'<img src="data:image/png;base64,{img_str}" width="180" height="180" />'
            return mark_safe(html)
        return "2FA not enabled"
    
    show_totp_qr.short_description = "TOTP QR Code"

# Contact model admin
class ContactAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'company', 'service']
    search_fields = ['first_name', 'last_name', 'email', 'company', 'service']

class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ["name","key","permission","is_active","last_request_at","request_count"]


admin.site.register(Contact, ContactAdmin)
admin.site.register(APIKey, ApiKeyAdmin)
