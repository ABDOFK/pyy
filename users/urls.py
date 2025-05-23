# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    # URLs pour modifier les profils
    path('profile/freelance/update/', views.update_freelance_profile, name='update_freelance_profile'),
    path('profile/client/update/', views.update_client_profile, name='update_client_profile'),
]