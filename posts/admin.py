from django.contrib import admin
from .models import BlogPost, BlogView, Comment, PageView,APIKey,Category

admin.site.register(BlogView)
admin.site.register(Comment)
admin.site.register(PageView)
admin.site.register(Category)


class BlogPostAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.full_clean()  # This calls clean() and all field validators
        super().save_model(request, obj, form, change)

admin.site.register(BlogPost, BlogPostAdmin)

@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'key',"permission", 'is_active', 'created_at')
    readonly_fields = ('key',)

    def permission(self,obj):
        return obj.permission