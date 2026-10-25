from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q

from .models import Notification, NotificationRecipient
from .forms import NotificationForm, BulkNotificationForm
from .utils import send_notification_email
from apps.clubs.models import Club


class NotificationListView(LoginRequiredMixin, ListView):
    model = NotificationRecipient
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return NotificationRecipient.objects.filter(
            user=self.request.user
        ).select_related('notification', 'notification__sender').order_by(
            'is_read', '-notification__created_at'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = NotificationRecipient.objects.filter(
            user=self.request.user,
            is_read=False
        ).count()
        return context


class NotificationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Notification
    form_class = NotificationForm
    template_name = 'notifications/notification_form.html'
    success_url = reverse_lazy('notifications:list')
    
    def test_func(self):
        return self.request.user.is_admin() or self.request.user.is_coordinator()
    
    def form_valid(self, form):
        notification = form.save(commit=False)
        notification.sender = self.request.user
        notification.save()
        
        # Get recipients based on selection
        recipient_type = form.cleaned_data.get('recipient_type')
        recipients = []
        
        if recipient_type == 'all':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recipients = User.objects.filter(is_active=True)
        
        elif recipient_type == 'students':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recipients = User.objects.filter(role='STUDENT', is_active=True)
        
        elif recipient_type == 'coordinators':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recipients = User.objects.filter(role='COORDINATOR', is_active=True)
        
        elif recipient_type == 'club':
            club = form.cleaned_data.get('club')
            if club:
                recipients = club.members.filter(is_active=True)
        
        elif recipient_type == 'custom':
            recipients = form.cleaned_data.get('custom_users')
        
        # Create notification recipients
        notification_recipients = []
        for user in recipients:
            notification_recipients.append(
                NotificationRecipient(notification=notification, user=user)
            )
        
        NotificationRecipient.objects.bulk_create(notification_recipients)
        
        # Send emails if requested
        if form.cleaned_data.get('send_email'):
            for user in recipients:
                send_notification_email(user, notification)
        
        messages.success(
            self.request, 
            f'Notification sent to {len(recipients)} users successfully!'
        )
        
        return super().form_valid(form)


@login_required
def mark_as_read(request, pk):
    notification_recipient = get_object_or_404(
        NotificationRecipient,
        pk=pk,
        user=request.user
    )
    
    notification_recipient.is_read = True
    notification_recipient.read_at = timezone.now()
    notification_recipient.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:list')


@login_required
def mark_all_as_read(request):
    NotificationRecipient.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


@login_required
def delete_notification(request, pk):
    notification_recipient = get_object_or_404(
        NotificationRecipient,
        pk=pk,
        user=request.user
    )
    
    notification_recipient.delete()
    messages.success(request, 'Notification deleted.')
    
    return redirect('notifications:list')


@login_required
def get_unread_count(request):
    """API endpoint for real-time notification count"""
    count = NotificationRecipient.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def get_recent_notifications(request):
    """API endpoint for recent notifications"""
    notifications = NotificationRecipient.objects.filter(
        user=request.user
    ).select_related('notification', 'notification__sender').order_by(
        '-notification__created_at'
    )[:5]
    
    data = []
    for notif_recipient in notifications:
        notif = notif_recipient.notification
        data.append({
            'id': notif_recipient.id,
            'title': notif.title,
            'message': notif.message[:100],
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': notif_recipient.is_read,
            'link': notif.link or '#',
        })
    
    return JsonResponse({'notifications': data})