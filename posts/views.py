from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import BlogPost
import json

# blog/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.utils.timezone import now
from .models import Comment, PageView, BlogPost,get_location_from_ip
from accounts.models import Profile
from .serializers import (
    CommentSerializer,
    PageViewSerializer,
    BlogReadTimeSerializer,
    BlogPostListSerializer,
    CreateCommentSerializer
)
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods



def home(request):
    return JsonResponse({"status":"success"})

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    token = get_token(request)
    print("csrf token : ",token)
    return JsonResponse({'csrfToken': token})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


class BlogPostsListAPIView(APIView):
    def get(self, request):
        blogs = BlogPost.objects.all().order_by('-created_at')
        serializer = BlogPostListSerializer(blogs, many=True)
        print("Blog list serializer data:", serializer.data)
        return Response(serializer.data)


@csrf_exempt
@require_http_methods(["POST"])
def add_comment(request, slug):
    try:
        blog = BlogPost.objects.get(slug=slug)
        data = json.loads(request.body)
        
        print("Comment/Reply data:", data,Profile.objects.get(email=data['email']))
        # Use the same create serializer for both comments and replies
        serializer = CreateCommentSerializer(data=data, context={'blog': blog})
        
        if serializer.is_valid():
            comment = serializer.save(
                user=Profile.objects.get(email=data['email']),
                blog=blog
            )
            # Return the created comment/reply with full data
            response_serializer = CommentSerializer(comment)
            return JsonResponse(response_serializer.data, status=201)
        
        return JsonResponse(serializer.errors, status=400)
        
    except BlogPost.DoesNotExist:
        return JsonResponse({"error": "Blog not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_comments_by_slug(request, slug):
    """
    Returns all comments and their nested replies for a blog post.
    """
    try:
        blog = BlogPost.objects.get(slug=slug)
    except BlogPost.DoesNotExist:
        return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get only top-level comments (parent=None)
    comments = Comment.objects.filter(blog=blog, parent=None)
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_comment(slug):
    try:
        blog = BlogPost.objects.get(slug=slug)
    except BlogPost.DoesNotExist:
        return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)

    # Get only top-level comments (parent=None)
    comments = Comment.objects.filter(blog=blog, parent=None)
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

 
@api_view(['GET'])
@permission_classes([AllowAny])
def blog_list(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    serializer = BlogPostListSerializer(post)
    return Response(serializer.data, status=status.HTTP_200_OK)

@csrf_exempt
@require_http_methods(["POST"])
def track_view(request):
    """
    Tracks a unique page view for a specific path (one record per page).
    Also tracks IP addresses and location info.
    """
    try:
        data = json.loads(request.body)
        path = data.get("path")

        if not path:
            return JsonResponse({"success": False, "error": "Path is required"}, status=400)

        ip = get_client_ip(request)  # get visitor IP
        location_info = get_location_from_ip(ip)  # returns dict with city/region/country

        # Get or create page record
        page, created = PageView.objects.get_or_create(path=path)

        # Add view for this IP (only if not already counted)
        page.add_view(ip, location_info)

        # Return response
        response = {
            "success": True,
            "message": "View tracked successfully",
            "is_liked": ip in (page.liked_ips or []),
            "views": page.views_count,
            "likes": page.like_count,
            "total_read": page.total_read_time,
            "ave_read": page.average_read_time,
        }
        return JsonResponse(response, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def toggle_like(request):
    """
    Toggles like or dislike for a page based on the user's IP.
    """
    try:
        print("lkjasdlkfjalkdjf",request.body)
        if request.body == b'':
            return JsonResponse({"success":False,"error": "Body perameters are required"}, status=400)

        data = json.loads(request.body)
        path = data.get("path")
        print("The path is : ",path)

        if not path or path is None:
            return JsonResponse({"success":False,"error": "Path is required"}, status=400)

        ip = get_client_ip(request)

        pageview, created = PageView.objects.get_or_create(
            path=path,
            defaults={"ip_addresses": ip}
        )

        if request.user.is_authenticated:
            pageview.user = request.user
            pageview.save()

        if pageview.has_liked(ip):
            # Dislike (remove like)
            pageview.remove_like(ip)
            return JsonResponse({"success":True,"message": "Disliked", "likes": pageview.like_count}, status=200)
        else:
            # Like
            pageview.add_like(ip)
            return JsonResponse({"success":True,"message": "Liked", "likes": pageview.like_count}, status=200)

    except Exception as e:
        return JsonResponse({"success":False,"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def track_read_time(request):
    """
    Receives read time for a blog post and updates the PageView model per IP.
    """
    try:
        data = json.loads(request.body)
        path = data.get("path")
        read_time = data.get("read_time")  # seconds

        if not path or not read_time:
            return JsonResponse({"success": False, "error": "Path and read_time required"}, status=400)

        ip = get_client_ip(request)

        page, created = PageView.objects.get_or_create(path=path)
        page.add_read_time(ip, int(read_time))
        print("The read time : ",page.total_read_time)

        return JsonResponse({
            "success": True,
            "message": "Read time updated",
            "total_read_time": page.total_read_time,
            "average_read_time": page.average_read_time
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
