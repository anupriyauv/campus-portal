from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.db.models import Avg, Count

from .models import Feedback
from .forms import FeedbackForm
from apps.events.models import Event, EventRegistration


class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'feedback/feedback_list.html'
    context_object_name = 'feedbacks'
    paginate_by = 20
    
    def get_queryset(self):
        event_slug = self.kwargs.get('event_slug')
        event = get_object_or_404(Event, slug=event_slug)
        
        queryset = Feedback.objects.filter(event=event).select_related('user', 'event')
        
        # Coordinators and admins can see all feedback
        if not (self.request.user.is_admin() or 
                event.club.coordinator == self.request.user):
            # Students only see non-anonymous feedback
            queryset = queryset.filter(
                Q(is_anonymous=False) | Q(user=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_slug = self.kwargs.get('event_slug')
        event = get_object_or_404(Event, slug=event_slug)
        
        context['event'] = event
        
        # Calculate statistics
        stats = Feedback.objects.filter(event=event).aggregate(
            avg_rating=Avg('rating'),
            avg_organization=Avg('organization_rating'),
            avg_content=Avg('content_rating'),
            avg_venue=Avg('venue_rating'),
            total_count=Count('id')
        )
        
        context['stats'] = stats
        
        # Rating distribution
        context['rating_distribution'] = []
        for i in range(5, 0, -1):
            count = Feedback.objects.filter(event=event, rating=i).count()
            percentage = (count / stats['total_count'] * 100) if stats['total_count'] > 0 else 0
            context['rating_distribution'].append({
                'rating': i,
                'count': count,
                'percentage': percentage
            })
        
        return context


@login_required
def submit_feedback(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)
    
    # Check if user attended the event
    try:
        registration = EventRegistration.objects.get(
            event=event,
            user=request.user,
            attended=True
        )
    except EventRegistration.DoesNotExist:
        messages.error(request, 'You can only provide feedback for events you attended.')
        return redirect('events:event_detail', slug=event_slug)
    
    # Check if feedback already submitted
    if Feedback.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, 'You have already submitted feedback for this event.')
        return redirect('events:event_detail', slug=event_slug)
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.event = event
            feedback.user = request.user
            feedback.save()
            
            messages.success(request, 'Thank you for your feedback!')
            return redirect('events:event_detail', slug=event_slug)
    else:
        form = FeedbackForm()
    
    context = {
        'form': form,
        'event': event,
    }
    
    return render(request, 'feedback/feedback_form.html', context)


@login_required
def my_feedback(request):
    feedbacks = Feedback.objects.filter(
        user=request.user
    ).select_related('event', 'event__club').order_by('-created_at')
    
    context = {
        'feedbacks': feedbacks,
    }
    
    return render(request, 'feedback/my_feedback.html', context)