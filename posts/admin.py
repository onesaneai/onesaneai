from django.contrib import admin
from .models import BlogPost, Category, Comment, PageView
from django_summernote.admin import SummernoteModelAdmin

class BlogPostAdmin(SummernoteModelAdmin):
    summernote_fields = ('content',)

admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(PageView)
