from django.contrib import admin
from .models import BlogPost, Category, Comment, PageView,APIKey
from django_summernote.admin import SummernoteModelAdmin

class BlogPostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)

class ApiKeyAdmin(SummernoteModelAdmin):
    list_display = ["name","key","permission","is_active","created_at","last_request_at"]

admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(PageView)
admin.site.register(APIKey,ApiKeyAdmin)
