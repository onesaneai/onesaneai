from django.contrib import admin
from django.urls import path
from .views import send_otp,save_contact,verify_otp,current_user,logout_view

# from django.contrib.auth import get_user_model
# user = get_user_model()
from .forms import CustomAdminAuthenticationForm
from .views import custom_admin_login
# Override the default admin login view to use our form
admin.site.login_form = CustomAdminAuthenticationForm
# 

urlpatterns = [
    path("admin/login/", custom_admin_login, name="admin_login"),
    path("send-otp/", send_otp, name="send_otp"),
    path("verify-otp/", verify_otp, name="verify_otp"),
    path("get-user/", current_user, name="get_user"),
    path("logout/", logout_view, name="logout"),
    path('contact/', save_contact, name='save_contact'),
]
