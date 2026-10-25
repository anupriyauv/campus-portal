from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone

from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegistrationForm, CustomLoginForm, UserProfileForm
from .models import User
from apps.events.models import Event, EventRegistration
from apps.clubs.models import Club, ClubMembership
from apps.notifications.models import Notification, NotificationRecipient
from .utils import log_audit_event


class RegisterView(CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.role = 'STUDENT'
        user.save()
        messages.success(self.request, 'Registration successful! Please login.')
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                log_audit_event(user, 'LOGIN', ip_address=request.META.get('REMOTE_ADDR'))
                messages.success(request, f'Welcome back, {user.first_name}!')
                if user.is_admin():
                    return redirect('accounts:admin_dashboard')
                else:
                    return redirect('accounts:dashboard')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    log_audit_event(request.user, 'LOGOUT', ip_address=request.META.get('REMOTE_ADDR'))
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    user = request.user
    context = {}
    
    # Common data for all users
    upcoming_events = Event.objects.filter(
        status='PUBLISHED',
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')[:5]
    
    context['upcoming_events'] = upcoming_events
    
    if user.is_admin():
        # Admin Dashboard
        context['total_users'] = User.objects.count()
        context['total_clubs'] = Club.objects.count()
        context['total_events'] = Event.objects.count()
        context['active_events'] = Event.objects.filter(
            status='PUBLISHED',
            start_datetime__gte=timezone.now()
        ).count()
        context['all_clubs'] = Club.objects.all().order_by('name')
        context['all_events'] = Event.objects.all().order_by('-start_datetime')
        
        # Recent registrations
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        
        # Event statistics
        context['event_stats'] = Event.objects.values('status').annotate(
            count=Count('id')
        )
        
        template = 'accounts/dashboard_admin.html'
    
    elif user.is_coordinator():
        # Coordinator Dashboard
        coordinated_clubs = Club.objects.filter(coordinator=user)
        context['coordinated_clubs'] = coordinated_clubs
        
        # Events organized by coordinator's clubs
        context['my_events'] = Event.objects.filter(
            club__in=coordinated_clubs
        ).order_by('-created_at')[:10]
        
        # Pending registrations for coordinator's events
        context['pending_registrations'] = EventRegistration.objects.filter(
            event__club__in=coordinated_clubs,
            status='PENDING'
        ).select_related('event', 'user')[:10]
        
        template = 'accounts/dashboard_coordinator.html'
    
    else:
        # Student Dashboard
        context['my_clubs'] = user.clubs.filter(is_active=True)
        
        # Registered events
        context['my_events'] = EventRegistration.objects.filter(
            user=user
        ).select_related('event').order_by('-registration_date')[:5]
        
        # Unread notifications
        context['unread_notifications'] = NotificationRecipient.objects.filter(
            user=user,
            is_read=False
        ).select_related('notification')[:5]
        
        # Suggested clubs (based on department or interests)
        context['suggested_clubs'] = Club.objects.filter(
            is_active=True
        ).exclude(
            members=user
        )[:4]
        
        template = 'accounts/dashboard_student.html'
    
    return render(request, template, context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user's clubs and events
    user_clubs = request.user.clubs.filter(is_active=True)
    user_events = EventRegistration.objects.filter(
        user=request.user
    ).select_related('event').order_by('-registration_date')[:10]
    
    context = {
        'form': form,
        'user_clubs': user_clubs,
        'user_events': user_events,
    }
    
    return render(request, 'accounts/profile.html', context)


class PublicProfileView(DetailView):
    model = User
    template_name = 'accounts/public_profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        context['user_clubs'] = user.clubs.filter(is_active=True)
        context['user_events'] = EventRegistration.objects.filter(
            user=user,
            status='ATTENDED'
        ).select_related('event')[:10]
        
        return context