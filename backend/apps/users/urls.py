from django.urls import path
from apps.users import views

urlpatterns = [
    path('users/', views.get_users, name='users'),
    path('register/', views.register_user, name='register-user'),
    path('login/', views.login_user, name='login-user'),
    path('refresh/', views.refresh, name='refresh'),
    path('profile/', views.user_profile, name='profile'),
]