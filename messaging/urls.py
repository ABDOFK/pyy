# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Liste des conversations de l'utilisateur
    path('', views.conversation_list_view, name='list'),
    # Détail d'une conversation spécifique
    path('conversation/<int:pk>/', views.conversation_detail_view, name='detail'),
    # Ajouter plus tard: url pour démarrer une nouvelle conversation
    path('start/<int:user_pk>/', views.start_conversation_view, name='start_conversation'),
]