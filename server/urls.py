from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from posts.models import BlogPost, Comment, PageView,APIKey,Category

# from two_factor.urls import urlpatterns as tf_urls

from django.contrib.auth import get_user_model
user = get_user_model()

# from django_otp.admin import OTPAdminSite
# from django_otp.plugins.otp_totp.models import TOTPDevice
# from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin

# class OTPAdmin (OTPAdminSite):
#     pass

# admin_site =OTPAdmin(name='OTPAdmin')
# admin_site.register(user)
# admin_site.register (TOTPDevice, TOTPDeviceAdmin)

# # Register your other models
# admin_site.register(BlogPost)
# admin_site.register(Comment)
# admin_site.register(PageView)
# admin_site.register(BlogView)
# admin_site.register(Category)

# admin_site.register(APIKey)
from server import views

urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),
    path('api/blogs/', include("posts.urls"), name='blog_list'),
    path('api/auth/', include("accounts.urls"), name='auth_user'),
    path('api/invoices/', include("invoices.urls"), name='invoice_list'),
    path('ckeditor/', include('ckeditor_uploader.urls'),name="multi_auth"),
]
# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
