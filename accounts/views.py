from django.shortcuts import render
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .serializers import ContactSerializer
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone   
from django.contrib.auth import login
from django.contrib.auth import logout
from datetime import timedelta
from rest_framework.exceptions import AuthenticationFailed

import random,time,requests,uuid
import json,random

TOKEN_EXPIRATION_HOURS = 24  # token valid for 24 hours


# auth/views.py
User = get_user_model()

def verify_token(key):
    try:
        token = Token.objects.get(key=key)
    except Token.DoesNotExist:
        raise AuthenticationFailed('Invalid token')

    if token.created + timedelta(hours=TOKEN_EXPIRATION_HOURS) < timezone.now():
        return {"success": False, "message": 'Token has expired'}
    
    return {"success": True, "user": token.user}


@api_view(["POST"])
@permission_classes([AllowAny])
def send_otp(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        name = data.get("name", "")
        print("The data is : ",data)
    
        if not email:
            return Response({"success": False, "message": "Email is required"})
        
        user = User.objects.filter(email=email, is_verified=True)
        if user.exists():
            name  = user[0].get_full_name().capitalize() or user[0].username

        otp = random.randint(100000, 999999)
        cache.set(f"otp_{email}", otp, timeout=90)  # 1.5 min expiry

        send_otp_email(email, name, otp)

        return Response({"success": True, "message": "OTP sent to email"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"success": False, "error": "Failed to send OTP"})

def send_otp_email(user_email,name, otp_code):
    """Send OTP verification email"""
    
    # Render the HTML template
    html_message = render_to_string('email_otp.html', {
        'otp_code': otp_code,
        'name': name
    })
    
    # Send email
    send_mail(
        subject='Verify Your Email - Onesane AI',
        message=f'Your verification code is: {otp_code}',  # Plain text fallback
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        html_message=html_message,
        fail_silently=False,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    data = json.loads(request.body)
    email = data.get("email")
    otp = data.get("otp")
    name = data.get("name", "")

    if not email or not otp:
        return Response({"success": False, "error": "Email and OTP are required"})

    cached_otp = cache.get(f"otp_{email}")
    print("The catched otp : ",cached_otp)

    if str(cached_otp) != str(otp) or cached_otp is None:
        return Response({"success": False, "error": "OTP is expired! send a new one."})

    # Get or create user
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"username": email.split("@")[0], "first_name": name, "is_verified": True}
    )
    if user.is_verified == False:
        user.is_verified = True
        user.save()

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)  # This must set Set-Cookie: sessionid=...
    # Delete OTP after successful login
    cache.delete(f"otp_{email}")
    # Set token expiry by adjusting the 'created' field (not recommended, as it's auto_now_add)
    # Instead, you should check expiry when verifying the token, not when creating it.
    # But if you want to set a custom expiry date, you need to update the field after creation.
    token, created = Token.objects.get_or_create(user=user)
    # Update the 'created' field to now + 2 days (for demonstration, not recommended for production)
    token.created = timezone.now() + timedelta(days=2)
    token.save()

    return Response({
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}".strip(),
        },
        "token": token.key
    })

def verify_recaptcha(token):
    # Verify token with Google
    resp = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={
            "secret":'6LcovOgrAAAAAHR1q4BqkPv1EgJLiphsShDrH9jX',
            "response": token,
        },
    )
    result = resp.json()
    print("The recaptcha result is : ",result)

    if not result.get("success"):
        return False
    # You can also check the score if using reCAPTCHA v3
    if result.get("score", 0) < 0.5:  # Adjust threshold as needed
        return False

    return True

@csrf_exempt
def save_contact(request):

    if request.method != 'POST':
        return JsonResponse({"success": False, 'error': 'Only POST method allowed.'}, status=405)

    data = json.loads(request.body)
    recaptcha_token = data.get('recaptcha_token')
    if not verify_recaptcha(recaptcha_token):
        return JsonResponse({'success': False, 'error': 'Invalid reCAPTCHA. Please try again.'}, status=400)

    # Check if a contact with the same email and message already exists
    serializer = ContactSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        send_contact_form_notification(serializer.data)

        return JsonResponse({'success': True, 'message': 'Contact saved successfully.'},status=200)

    else:
        return JsonResponse({'success': False, 'error':"You already filled in the form with the same details."}, status=400)


def send_contact_form_notification(form_data):
    """Send contact form submission notification to admin"""
    try:
        # Generate unique submission ID
        submission_id = str(uuid.uuid4())[:8].upper()
        
        # Context for email template
        context = {
            'first_name': form_data.get('first_name', ''),
            'last_name': form_data.get('last_name', ''),
            'email': form_data.get('email', ''),
            'company': form_data.get('company', 'Not provided'),
            'service_interested': form_data.get('service', 'Not specified'),
            'message': form_data.get('message', ''),
            'submission_date': timezone.now().strftime('%B %d, %Y at %I:%M %p'),
            'submission_id': submission_id,
        }
        
        # Render HTML template
        html_message = render_to_string('email_contact.html', context)
        
        # Plain text version
        plain_message = f"""
        New Contact Form Submission
        
        Name: {context['first_name']} {context['last_name']}
        Email: {context['email']}
        Company: {context['company']}
        Service: {context['service_interested']}
        
        Message:
        {context['message']}
        
        Submission ID: #{submission_id}
        Date: {context['submission_date']}
        """
        
        # Send to admin(s)
        send_mail(
            subject=f'🔔 New Contact Form - {context["first_name"]} {context["last_name"]} ({context["service_interested"]})',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],  # or settings.ADMINS
            html_message=html_message,
            fail_silently=False,
        )
        
        return submission_id
    except Exception as e:
        print("Failed to send contact form email:", str(e))
        return None

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def current_user(request):
    try:
        data = json.loads(request.body)
        token  = data.get('token')
        print("The token is: ",token)
        tkuser = verify_token(token)
        print("The token user is : ",tkuser)

        if tkuser.get('success'):

            user = tkuser.get('user')

            return JsonResponse({
                'success':True,
                "user": {
                    "id": user.id,
                    "name": user.get_full_name() or user.username,
                    "email": user.email,
                    "username": user.username,
                }
            })
        else:
            return JsonResponse({'success':False,'message':"The session expired! Login again."})
    except Exception as r:
        return JsonResponse({'success':False,'message':"Failed to fetch user data."})

@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    try:
        data = json.loads(request.body)
        token  = data.get('token')
        # print("The token is: ",token)

        tkuser = verify_token(token)

        if tkuser.get('success'):
            user = tkuser.get('user')

            Token.objects.get(user=user).delete()
            print("The token user is value--- : ")

            logout(request)

        return JsonResponse({"success": True})
    except Exception as r:
        return JsonResponse({"success": False, "error": str(r)})

