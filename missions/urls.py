# missions/urls.py
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
    path('start/<int:user_pk>/', views.start_conversation_view, name='start_conversation'),
    # URL pour laisser une évaluation pour une mission
    path('<int:mission_pk>/evaluate/', views.leave_evaluation_view, name='leave_evaluation'),
]