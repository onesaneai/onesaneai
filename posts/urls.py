from django.urls import path
from . import views

urlpatterns = [
    path("",views.home,name="Home"),
    path("getall/",views.BlogPostsListAPIView.as_view(),name="list_all_posts"),
    path('get/<str:slug>/', views.blog_list, name='single_post'),

    path('<slug:slug>/comments/', views.list_comments_by_slug, name='list_comments_by_slug'),
    path('<slug:slug>/comments/add/new/', views.add_comment, name='add_comment'),

    path('readtime/', views.track_read_time, name='blog_read_time'),
    path('track-view/', views.track_view, name='track_view'),
    path('toggle-like/', views.toggle_like, name='toggle_like'),

    path('csrf/', views.get_csrf_token, name='csrf_token'),
]
