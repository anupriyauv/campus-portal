from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('event/<slug:event_slug>/', views.FeedbackListView.as_view(), name='event_feedback_list'),
    path('event/<slug:event_slug>/submit/', views.submit_feedback, name='submit_feedback'),
    path('my-feedback/', views.my_feedback, name='my_feedback'),
]