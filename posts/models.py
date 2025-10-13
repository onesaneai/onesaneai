from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image
import os,json

# Create your models here.
from django.utils.crypto import get_random_string
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from taggit.managers import TaggableManager
# from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
# models.py
from django.contrib.auth import get_user_model

User = get_user_model()

# Validaters for model fields
# ----------- Featured Image validation -------------------
def validate_image_file_extension(value):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f'Unsupported file extension. Allowed: {", ".join(valid_extensions)}')


STATUS_CHOICES = [('draft', 'Draft'),('published', 'Published'),]

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True,editable=False)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    excerpt = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    content = RichTextUploadingField()
    author = models.ForeignKey(User,on_delete=models.CASCADE,related_name='blog_posts')
    slug = models.SlugField(unique=True, max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(upload_to='blog/images/', blank=True, null=True)
    tags = TaggableManager()

    allow_comments = models.BooleanField(default=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO Title, max 60 characters.")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO Description, max 160 characters.")

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()

        if self.featured_image:
            # Size validation
            if self.featured_image.size > 1 * 1024 * 1024:  # 1MB
                raise ValidationError("Image size must be under 1MB.")

            # Optional: double check format with PIL (useful if content-type spoofed)
            try:
                image = Image.open(self.featured_image)
                if image.format not in ['JPEG', 'JPG', 'PNG', 'WEBP']:
                    raise ValidationError("Unsupported image format. Use JPEG, PNG, or WEBP.")
            except Exception:
                raise ValidationError("Uploaded file is not a valid image.")

    def __str__(self):
        return self.title

class BlogView(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(User,on_delete=models.SET_NULL, null=True, blank=True)

    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.blog.title} - {self.ip_address}"

class Comment(models.Model):
    blog = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user} on {self.blog}"


import requests

def get_location_from_ip(ip):
    """Fetch city, region, and country for an IP using ip-api."""
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json")
        data = response.json()
        if data.get("status") == "success":
            return {
                "city": data.get("city"),
                "region": data.get("regionName"),
                "country": data.get("country"),
                "postal": data.get("postal"),
                "country_capital": data.get("country_capital")
            }
    except:
        pass
    return {"city": None, "region": None, "country": None,"country_capital":None,"postal":None}


class PageView(models.Model):
    path = models.CharField(max_length=500)  # e.g. '/about/', '/contact/'
    # ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    address = models.TextField(default='',null=True,blank=True)
    # Likes tracked via IP addresses
    ip_addresses = models.JSONField(default=list, blank=True, null=True)  # all unique visitors
    liked_ips = models.JSONField(default=list, blank=True)  # Stores list of IPs who liked
    read_times = models.JSONField(default=dict, blank=True, null=True)   # stores read time per IP


    def __str__(self):
        return f"{self.path} viewed by {self.ip_addresses}"

    # ================= Read Time ============================ 
    def add_read_time(self, ip, seconds):
        """Add read time for an IP. Accumulates if multiple visits."""
        if not self.read_times:
            self.read_times = {}
        current = self.read_times.get(ip, 0)
        self.read_times[ip] = current + seconds
        self.save()
    
    @property
    def total_read_time(self):
        """Sum of read times across all IPs."""
        return sum(self.read_times.values()) if self.read_times else 0
        
    @property
    def average_read_time(self):
        """Average read time per unique visitor."""
        if not self.read_times:
            return 0
        return sum(self.read_times.values()) / len(self.read_times)

    # ====================== Page Views =========================================

    def add_view(self, ip, location=None):
        """Add a view if IP is new."""
        if ip not in self.ip_addresses:
            self.ip_addresses.append(ip)
            if location:
                self.address = json.dumps(location)  # optional: store last visitor location
            self.save()

    @property
    def views_count(self):
        return len(self.ip_addresses)

    # ====================== Page Likes =========================================

    @property
    def like_count(self):
        """Return the number of unique likes for this page."""
        return len(self.liked_ips)

    def add_like(self, ip):
        """Add a like for this IP if not already liked."""
        if ip not in self.liked_ips:
            self.liked_ips.append(ip)
            self.save()

    def remove_like(self, ip):
        """Remove a like for this IP if already liked."""
        if ip in self.liked_ips:
            self.liked_ips.remove(ip)
            self.save()

    def has_liked(self, ip):
        """Check if this IP has already liked the page."""
        return ip in self.liked_ips

 
class APIKey(models.Model):
    PERMISSION_CHOICES = [
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
    ]

    name = models.CharField(max_length=100, unique=True)
    key = models.CharField(max_length=40, unique=True, editable=False)
    permission = models.CharField(max_length=5, choices=PERMISSION_CHOICES, default='read')
    rate_limit_per_minute = models.PositiveIntegerField(default=60)  # default 60 requests/min
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_request_at = models.DateTimeField(null=True, blank=True)
    request_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = get_random_string(length=40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.permission})"

