from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Invoice, Client,CompanyInfo
from .forms import InvoiceForm, InvoiceItemFormSet,InvoiceItem
import random,json
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from accounts.views import send_otp_email
from django.contrib.auth import login,logout
User = get_user_model()



def admin_only(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(admin_only)
def create_invoice_view(request):
    """Create and preview invoices dynamically"""
    if request.method == "POST":
        form = InvoiceForm(request.POST)
        formset = InvoiceItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.status = "draft"
            invoice.save()
            formset.instance = invoice
            formset.save()
            invoice.update_totals()

            if "preview" in request.POST:
                preview_html = render_to_string("invoices/_preview.html", {"invoice": invoice})
                return JsonResponse({"preview": preview_html})
            elif "send" in request.POST:
                # send email logic (placeholder)
                return JsonResponse({"success": True, "message": "Invoice sent successfully!"})
            elif "save" in request.POST:
                return redirect("create_invoice")

    else:
        form = InvoiceForm()
        formset = InvoiceItemFormSet()

    return render(request, "invoices/invoice_create.html", {
        "form": form,
        "formset": formset,
    })

@login_required
@user_passes_test(admin_only)
def preview_invoice_view(request, invoice_number):
    """Preview a specific invoice by its number"""
    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    company = get_object_or_404(CompanyInfo)
    items = InvoiceItem.objects.filter(invoice=invoice)
    print("Previewing invoice:", invoice)
    return render(request, "invoices/_preview.html", {"invoice": invoice, "company": company, "items": items})

@login_required
@user_passes_test(admin_only)
def share_invoice_view(request, invoice_number):
    """Share invoice via email (placeholder implementation)"""

    if request.method == "POST":

        invoice = get_object_or_404(Invoice, invoice_number=invoice_number)

        username = invoice.client.email.split('@')[0]
        email = invoice.client.email
        first_name = invoice.client.company_name.split(' ')[0]
        last_name = ' '.join(invoice.client.company_name.split(' ')[1:]) if len(invoice.client.company_name.split(' ')) > 1 else ''

        user, created = User.objects.get_or_create(username=username, defaults={'email': email, 'first_name': first_name, 'last_name': last_name})
        print("User for invoice:", user)
        return JsonResponse({"success": True, "message": "Invoice shared successfully!", "email": email,"name":invoice.client.company_name})

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

def shared_invoice_preview_view(request, invoice_number):
    """Preview a shared invoice (publicly accessible)"""

    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        print("User is authenticated:", request.user)
        return redirect('get_invoice', invoice_number=invoice_number)

    invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
    company = get_object_or_404(CompanyInfo)
    items = InvoiceItem.objects.filter(invoice=invoice)
    print("Shared previewing invoice:", invoice)
    return render(request, "invoices/shared_invoice_preview.html", {"invoice": invoice, "company": company, "items": items})

def send_otp_view(request, invoice_number):
    """Send OTP to client's email for accessing shared invoice"""
    if request.method == "POST":
        invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
        data = json.loads(request.body)
        client_email = data.get("email")

        if client_email and client_email == invoice.client.email:
            # Generate a simple OTP (for demonstration purposes)
            otp = str(random.randint(100000, 999999))  # In production, generate a random OTP and store it securely

            otp = random.randint(100000, 999999)
            cache.set(f"otp_{client_email}", otp, timeout=90)  # 1.5 min expiry

            send_otp_email(client_email, invoice.client.company_name, otp)

            return JsonResponse({"success": True, "message": "OTP sent to your email."})
        else:
            return JsonResponse({"success": False, "error": "Email does not match our records."}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

def verify_otp_view(request, invoice_number):
    """Verify OTP for accessing shared invoice"""
    if request.method == "POST":
        invoice = get_object_or_404(Invoice, invoice_number=invoice_number)
        data = json.loads(request.body)
        client_email = data.get("email")
        otp = data.get("otp")

        if not client_email or not otp:
            return JsonResponse({"success": False, "error": "Email and OTP are required."})

        cached_otp = cache.get(f"otp_{client_email}")

        if str(cached_otp) != str(otp) or cached_otp is None:
            return JsonResponse({"success": False, "error": "OTP is expired or invalid! Please request a new one."})

        if client_email == invoice.client.email:
            login(request,User.objects.get(email=client_email), backend='django.contrib.auth.backends.ModelBackend')
            return JsonResponse({"success": True,"otp_verified": True})
        else:
            return JsonResponse({"success": False, "error": "Email does not match our records."})

    return JsonResponse({"success": False, "error": "Invalid request method."})

def logout_view(request, invoice_number):
    """Logout the user and redirect to homepage"""
    logout(request)
    return redirect('shared_invoice_preview', invoice_number=invoice_number)
