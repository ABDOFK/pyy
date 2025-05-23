# missions/urls.py - Version mise à jour avec le suivi
from django.urls import path
from . import views

app_name = 'missions'

urlpatterns = [
    path('', views.mission_list_view, name='list'),
    path('<int:pk>/', views.mission_detail_view, name='detail'),
    path('create/', views.create_mission_view, name='create'),
    path('my-missions/', views.my_missions_view, name='my_missions'),

    # URLs pour les candidatures
    path('<int:mission_pk>/apply/', views.apply_to_mission_view, name='apply'),
    path('my-applications/', views.my_applications_view, name='my_applications'),
    path('<int:mission_pk>/candidatures/', views.view_candidatures_view, name='view_candidatures'),
    path('candidature/<int:candidature_pk>/accept/', views.accept_candidature_view, name='accept_candidature'),
    path('candidature/<int:candidature_pk>/reject/', views.reject_candidature_view, name='reject_candidature'),
    
    # URLs pour les évaluations
    path('<int:mission_pk>/evaluate/', views.leave_evaluation_view, name='leave_evaluation'),
    
    # URLs pour le suivi d'avancement
    path('tracking/', views.mission_tracking_dashboard, name='tracking_dashboard'),
    path('<int:pk>/tracking/', views.mission_tracking_detail, name='tracking_detail'),
    path('<int:pk>/update-progress/', views.update_mission_progress, name='update_progress'),
    path('<int:pk>/update-status/', views.update_mission_status, name='update_status'),
    path('<int:pk>/add-milestone/', views.add_milestone, name='add_milestone'),
    path('<int:pk>/milestone/<int:milestone_id>/toggle/', views.toggle_milestone, name='toggle_milestone'),
    path('<int:pk>/add-comment/', views.add_comment, name='add_comment'),
]