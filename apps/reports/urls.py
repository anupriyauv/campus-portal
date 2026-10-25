from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('event/<slug:slug>/', views.event_report, name='event_report'),
    path('event/<slug:slug>/export/', views.export_event_report, name='export_event_report'),
    path('club/<slug:slug>/', views.club_report, name='club_report'),
    path('club/<slug:slug>/export/', views.export_club_report, name='export_club_report'),
]