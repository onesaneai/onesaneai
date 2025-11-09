from django.urls import path
from .views import create_invoice_view,preview_invoice_view, share_invoice_view,shared_invoice_preview_view,send_otp_view,verify_otp_view,logout_view
urlpatterns = [
    path('create/', create_invoice_view, name='create_invoice'),
    path('<str:invoice_number>/update/', create_invoice_view, name='update_invoice'),
    path('<str:invoice_number>/delete/', create_invoice_view, name='delete_invoice'),
    path('<str:invoice_number>/share/', share_invoice_view, name='share_invoice'),
    path('<str:invoice_number>/preview/shared/send-otp/', send_otp_view, name='send_otp'),
    path('<str:invoice_number>/preview/shared/verify-otp/', verify_otp_view, name='verify_otp'),
    path('<str:invoice_number>/preview/', preview_invoice_view, name='get_invoice'),
    path('<str:invoice_number>/preview/shared/', shared_invoice_preview_view, name='shared_invoice_preview'),
    path('<str:invoice_number>/preview/shared/logout/', logout_view, name='shared_invoice_logout'),
    path('<str:invoice_number>/download/', create_invoice_view, name='download_invoice')
]