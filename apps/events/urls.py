from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('my-events/', views.my_events, name='my_events'),
    path('<slug:slug>/update/', views.EventUpdateView.as_view(), name='event_update'),
    path('<slug:slug>/register/', views.register_event, name='register_event'),
    path('<slug:slug>/cancel-registration/', views.cancel_registration, name='cancel_registration'),
    path('calendar/', views.event_calendar, name='event_calendar'),
    path('<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<slug:slug>/photos/upload/', views.upload_event_photos, name='upload_event_photos'),
    path('<slug:slug>/results/add/', views.add_event_results, name='add_event_results'),
    path('<slug:slug>/registrations/', views.EventRegistrationListView.as_view(), name='event_registration_list'),
    path('registrations/<int:pk>/update/', views.EventRegistrationUpdateView.as_view(), name='event_registration_update'),
    path('<slug:slug>/announcements/add/', views.add_event_announcement, name='add_event_announcement'),
]