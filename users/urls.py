# users/urls.py - Version mise à jour
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
    
    # URLs pour la recherche de freelances
    path('freelances/', views.freelance_search_view, name='freelance_search'),
    path('freelance/<int:user_id>/', views.freelance_profile_view, name='freelance_profile'),
]