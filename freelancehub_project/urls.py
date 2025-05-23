# freelancehub_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),

    # --- Décommentez ou ajoutez cette ligne ---
    path('missions/', include('missions.urls', namespace='missions')),

    # path('payments/', include('payments.urls', namespace='payments')),

    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]