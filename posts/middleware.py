from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import APIKey

class APIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow OPTIONS requests to proceed without a key for preflight checks.
        if request.method == 'OPTIONS':
            return self.get_response(request)

        # Define public API paths that do not require an API key.
        public_paths = ['/api/invoices', '/api/auth/', '/admin/']

        # Check if the request path starts with any of the public paths.
        is_public = any(request.path.startswith(path) for path in public_paths)
        if is_public:
            return self.get_response(request)

        # For all other paths under /api/, an API key is required.
        if request.path.startswith('/api/'):
            api_key = request.headers.get('X-API-KEY')
            if not api_key:
                return JsonResponse({'error': 'API key missing'}, status=401)

            try:
                key_obj = APIKey.objects.get(key=api_key, is_active=True)
            except APIKey.DoesNotExist:
                return JsonResponse({'error': 'Invalid API key'}, status=403)

            # Check permission: if the request is a write operation (not GET, HEAD, or OPTIONS)
            # and the key is read-only, deny access.
            if request.method not in ['GET', 'HEAD'] and key_obj.permission == 'read':
                return JsonResponse({'error': 'API key does not have write permission'}, status=403)

            # Rate limiting logic
            now = timezone.now()
            # If the last request was within the last minute
            if key_obj.last_request_at and (now - key_obj.last_request_at) < timedelta(minutes=1):
                if key_obj.request_count >= key_obj.rate_limit_per_minute:
                    return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
                key_obj.request_count += 1
            else:
                # If it's been more than a minute, reset the counter.
                key_obj.request_count = 1

            key_obj.last_request_at = now
            key_obj.save()

        # If all checks pass, proceed to the view.
        return self.get_response(request)
