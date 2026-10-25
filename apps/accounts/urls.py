from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin/dashboard/', views.dashboard_view, name='admin_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.PublicProfileView.as_view(), name='public_profile'),
]