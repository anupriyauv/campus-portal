from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse

from .models import Event, EventRegistration, EventPhoto, EventResult, EventAnnouncement
from .forms import EventForm, EventPhotoForm, EventResultForm
from apps.accounts.utils import log_audit_event
from apps.events.forms import EventAnnouncementForm
from apps.notifications.models import Notification, NotificationRecipient


class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Event.objects.filter(
            status='PUBLISHED'
        ).select_related('club', 'organizer').annotate(
            registration_count=Count('participants')
        )
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(club__name__icontains=search_query)
            )
        
        # Filter by type
        event_type = self.request.GET.get('type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by time
        time_filter = self.request.GET.get('time', 'upcoming')
        now = timezone.now()
        
        if time_filter == 'upcoming':
            queryset = queryset.filter(start_datetime__gte=now)
        elif time_filter == 'past':
            queryset = queryset.filter(end_datetime__lt=now)
        elif time_filter == 'today':
            queryset = queryset.filter(
                start_datetime__date=now.date()
            )
        
        return queryset.order_by('start_datetime')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_types'] = Event.TYPE_CHOICES
        context['selected_type'] = self.request.GET.get('type', '')
        context['time_filter'] = self.request.GET.get('time', 'upcoming')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Featured events
        context['featured_events'] = Event.objects.filter(
            status='PUBLISHED',
            is_featured=True,
            start_datetime__gte=timezone.now()
        )[:3]
        
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()
        
        # Check if user is registered
        if self.request.user.is_authenticated:
            context['is_registered'] = EventRegistration.objects.filter(
                event=event,
                user=self.request.user
            ).exists()
            
            if context['is_registered']:
                context['registration'] = EventRegistration.objects.get(
                    event=event,
                    user=self.request.user
                )
        
        # Event photos
        context['photos'] = event.photos.all()[:12]
        
        # Event results
        context['results'] = event.results.select_related('participant').order_by('position')
        
        # Event announcements
        context['announcements'] = event.announcements.all()
        
        # Similar events
        context['similar_events'] = Event.objects.filter(
            club=event.club,
            status='PUBLISHED'
        ).exclude(id=event.id).order_by('-created_at')[:3]
        
        return context


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    
    def test_func(self):
        return self.request.user.is_coordinator()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'CREATE', model_name='Event', object_id=self.object.id, object_repr=self.object.title, ip_address=self.request.META.get('REMOTE_ADDR'))
        messages.success(self.request, 'Event created successfully!')

        # Create a notification for all students about the new event
        if form.instance.status == 'PUBLISHED':
            notification = Notification.objects.create(
                message=f'New event published: {form.instance.title}',
                link=reverse_lazy('events:event_detail', kwargs={'slug': form.instance.slug}),
                notification_type='NEW_EVENT'
            )
            # Assuming a 'Student' group or similar way to identify students
            # For simplicity, let's assume all users are potential recipients for now
            # In a real app, you'd filter by user type or subscription
            from django.contrib.auth import get_user_model
            User = get_user_model()
            students = User.objects.filter(role='STUDENT') # Assuming a 'role' field in User model
            for student in students:
                NotificationRecipient.objects.create(notification=notification, user=student)

        return response
    
    def get_success_url(self):
        return reverse_lazy('events:event_detail', kwargs={'slug': self.object.slug})


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def test_func(self):
        event = self.get_object()
        return (event.club.coordinator == self.request.user or
                event.organizer == self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'UPDATE', model_name='Event', object_id=self.object.id, object_repr=self.object.title, change_message='Event details updated', ip_address=self.request.META.get('REMOTE_ADDR'))
        messages.success(self.request, 'Event updated successfully!')
        return response
    
    def get_success_url(self):
        return reverse_lazy('events:event_detail', kwargs={'slug': self.object.slug})


@login_required
def register_event(request, slug):
    if not request.user.is_student():
        messages.error(request, 'Only students can register for events.')
        return redirect('events:event_detail', slug=slug)

    event = get_object_or_404(Event, slug=slug)
    
    if not event.is_registration_open():
        messages.error(request, 'Registration for this event is closed or full.')
        return redirect('events:event_detail', slug=slug)

    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, 'You are already registered for this event.')
    else:
        EventRegistration.objects.create(
            event=event,
            user=request.user,
            status='CONFIRMED' # Assuming immediate confirmation
        )
        log_audit_event(request.user, 'REGISTER_EVENT', model_name='EventRegistration', object_id=event.id, object_repr=event.title, change_message=f'Registered for event {event.title}', ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'You have successfully registered for {event.title}!')
    
    return redirect('events:event_detail', slug=slug)


@login_required
def cancel_registration(request, slug):
    if not request.user.is_student():
        messages.error(request, 'Only students can cancel event registrations.')
        return redirect('events:event_detail', slug=slug)

    event = get_object_or_404(Event, slug=slug)
    
    if not event.is_registration_open():
        messages.error(request, 'Cannot cancel registration for this event as it is closed or has already occurred.')
        return redirect('events:event_detail', slug=slug)

    try:
        membership = EventRegistration.objects.get(event=event, user=request.user)
        membership.delete()
        log_audit_event(request.user, 'CANCEL_EVENT_REGISTRATION', model_name='EventRegistration', object_id=event.id, object_repr=event.title, change_message=f'Cancelled registration for event {event.title}', ip_address=request.META.get('REMOTE_ADDR'))
        messages.success(request, f'You have cancelled your registration for {event.title}.')
    except EventRegistration.DoesNotExist:
        messages.error(request, 'You are not registered for this event.')
    
    return redirect('events:event_detail', slug=slug)


@login_required
def my_events(request):
    registrations = EventRegistration.objects.filter(
        user=request.user
    ).select_related('event', 'event__club').order_by('-registration_date')
    
    # Separate by status
    upcoming = registrations.filter(
        event__start_datetime__gte=timezone.now(),
        status='CONFIRMED'
    )
    
    past = registrations.filter(
        event__end_datetime__lt=timezone.now()
    )
    
    cancelled = registrations.filter(status='CANCELLED')
    
    context = {
        'upcoming': upcoming,
        'past': past,
        'cancelled': cancelled,
    }
    
    return render(request, 'events/my_events.html', context)


@login_required
def event_calendar(request):
    events = Event.objects.filter(
        status='PUBLISHED',
        start_datetime__gte=timezone.now()
    ).select_related('club')
    
    # Format events for FullCalendar
    events_data = []
    for event in events:
        events_data.append({
            'title': event.title,
            'start': event.start_datetime.isoformat(),
            'end': event.end_datetime.isoformat(),
            'url': event.get_absolute_url() if hasattr(event, 'get_absolute_url') else f'/events/{event.slug}/',
            'color': '#007bff',
        })
    
    context = {
        'events_json': events_data,
    }
    
    return render(request, 'events/event_calendar.html', context)


@login_required
def upload_event_photos(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check permissions
    if not (request.user.is_admin() or 
            event.club.coordinator == request.user or
            event.organizer == request.user):
        messages.error(request, 'You do not have permission to upload photos.')
        return redirect('events:event_detail', slug=slug)
    
    if request.method == 'POST':
        form = EventPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.event = event
            photo.uploaded_by = request.user
            photo.save()
            messages.success(request, 'Photo uploaded successfully!')
            return redirect('events:event_detail', slug=slug)
    else:
        form = EventPhotoForm()
    
    context = {
        'event': event,
        'form': form,
        'photos': event.photos.all(),
    }
    
    return render(request, 'events/upload_photos.html', context)


@login_required
def add_event_results(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check permissions
    if not (request.user.is_admin() or 
            event.club.coordinator == request.user or
            event.organizer == request.user):
        messages.error(request, 'You do not have permission to add results.')
        return redirect('events:event_detail', slug=slug)
    
    if request.method == 'POST':
        form = EventResultForm(request.POST)
        if form.is_valid():
            result = form.save(commit=False)
            result.event = event
            result.save()
            messages.success(request, 'Result added successfully!')
            return redirect('events:add_event_results', slug=slug)
    else:
        form = EventResultForm()
        # Filter participants to only registered users
        form.fields['participant'].queryset = event.participants.filter(
            eventregistration__status='ATTENDED'
        )
    
    context = {
        'event': event,
        'form': form,
        'results': event.results.select_related('participant').order_by('position'),
    }
    
    return render(request, 'events/add_results.html', context)


class EventRegistrationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = EventRegistration
    template_name = 'events/event_registration_list.html'
    context_object_name = 'registrations'
    paginate_by = 20

    def get_queryset(self):
        self.event = get_object_or_404(Event, slug=self.kwargs['slug'])
        queryset = EventRegistration.objects.filter(event=self.event).select_related('user')

        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )

        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by('-registration_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['registration_statuses'] = EventRegistration.STATUS_CHOICES
        return context

    def test_func(self):
        event = get_object_or_404(Event, slug=self.kwargs['slug'])
        return (self.request.user.is_admin() or
                event.club.coordinator == self.request.user or
                event.organizer == self.request.user)


class EventRegistrationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = EventRegistration
    fields = ['status']
    template_name = 'events/event_registration_update.html'
    context_object_name = 'registration'
    pk_url_kwarg = 'pk'

    def get_success_url(self):
        return reverse_lazy('events:event_registration_list', kwargs={'slug': self.object.event.slug})

    def test_func(self):
        registration = self.get_object()
        return (self.request.user.is_admin() or
                registration.event.club.coordinator == self.request.user or
                registration.event.organizer == self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'UPDATE', model_name='EventRegistration', object_id=self.object.id, object_repr=f'Registration for {self.object.event.title} by {self.object.user.username}', change_message=f'Status updated to {self.object.status}', ip_address=self.request.META.get('REMOTE_ADDR'))
        messages.success(self.request, 'Registration status updated successfully!')
        return response


@login_required
def add_event_announcement(request, slug):
    event = get_object_or_404(Event, slug=slug)

    # Check permissions
    if not (request.user.is_admin() or
            event.club.coordinator == request.user or
            event.organizer == request.user):
        messages.error(request, 'You do not have permission to add announcements.')
        return redirect('events:event_detail', slug=slug)

    if request.method == 'POST':
        form = EventAnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.event = event
            announcement.save()
            messages.success(request, 'Announcement added successfully!')
            return redirect('events:event_detail', slug=slug)
    else:
        form = EventAnnouncementForm()

    context = {
        'event': event,
        'form': form,
        'announcements': event.announcements.all(),
    }

    return render(request, 'events/add_announcement.html', context)