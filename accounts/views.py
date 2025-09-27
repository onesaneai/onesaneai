from django.shortcuts import render

# Create your views here.
import random,time
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
import json,random
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import Profile,Contact
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

        otp = random.randint(100000, 999999)
        cache.set(f"otp_{email}", otp, timeout=90)  # 1.5 min expiry

        send_mail(
            subject="Your Login Code",
            message=f"Your verification code is {otp}",
            from_email="noreply@example.com",
            recipient_list=[email],
        )

        return Response({"success": True, "message": "OTP sent to email"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"success": False, "error": "Failed to send OTP"})


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

 
@csrf_exempt
def save_contact(request):
    print("The user info : ",request.body)
    time.sleep(2)
    if request.method != 'POST':
        return JsonResponse({"success": False, 'error': 'Only POST method allowed.'}, status=405)

    data = json.loads(request.body)
    serializer = ContactSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return JsonResponse({'success': True, 'message': 'Contact saved successfully.'},status=200)
    else:
        return JsonResponse({'success': False, 'error':"You already filled in the form with the same details."}, status=400)
    

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
