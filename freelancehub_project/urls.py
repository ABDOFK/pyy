# freelancehub_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('missions/', include('missions.urls', namespace='missions')),
    path('messaging/', include('messaging.urls', namespace='messaging')),
    # path('payments/', include('payments.urls', namespace='payments')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]