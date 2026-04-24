from django.urls import path
from .views import *

urlpatterns = [
    #path('', index, name='index'),
    path('login', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('follow/<int:user_id>/', toggle_follow, name='toggle_follow'),
]