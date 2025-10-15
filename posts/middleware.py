from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import APIKey

class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
        # Skip OPTIONS requests
        if request.method == 'OPTIONS':
            return self.get_response(request)

        if request.path.startswith('/api/'):
            api_key = request.headers.get('X-API-KEY')
            if not api_key:
                return JsonResponse({'error': 'API key missing'}, status=401)

            try:
                key_obj = APIKey.objects.get(key=api_key, is_active=True)
            except APIKey.DoesNotExist:
                return JsonResponse({'error': 'Invalid API key'}, status=403)

            # Check permission
            if request.method not in ['GET', 'HEAD', 'OPTIONS'] and key_obj.permission == 'read':
                return JsonResponse({'error': 'API key does not have write permission'}, status=403)

            # Rate limiting (per minute)
            now = timezone.now()
            if key_obj.last_request_at and key_obj.last_request_at + timedelta(minutes=1) > now:
                if key_obj.request_count >= key_obj.rate_limit_per_minute:
                    return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
                key_obj.request_count += 1
            else:
                # Reset counter
                key_obj.request_count = 1
                key_obj.last_request_at = now
            key_obj.save()

        response = self.get_response(request)
        return response
