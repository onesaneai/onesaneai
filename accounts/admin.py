from django.contrib import admin
from .models import Profile,Contact
# Register your models here.
# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

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
    list_display = ['email', 'username', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'groups']

    fieldsets = (
        (_('Login Info'), {
            'fields': ('email', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('username', 'first_name', 'last_name','date_of_birth','city','country', 'profile_image')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )

    search_fields = ['email', 'username']

# Contact model admin
class ContactAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'company', 'service']
    search_fields = ['first_name', 'last_name', 'email', 'company', 'service']

admin.site.register(Contact, ContactAdmin)