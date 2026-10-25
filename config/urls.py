from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('clubs/', include('apps.clubs.urls', namespace='clubs')),
    path('events/', include('apps.events.urls', namespace='events')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('feedback/', include('apps.feedback.urls', namespace='feedback')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)