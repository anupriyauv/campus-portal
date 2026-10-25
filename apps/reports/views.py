from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta
import json

from apps.events.models import Event, EventRegistration
from apps.clubs.models import Club, ClubMembership
from apps.feedback.models import Feedback
from django.contrib.auth import get_user_model

User = get_user_model()


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'reports/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_admin()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Overview statistics
        context['total_users'] = User.objects.count()
        context['total_students'] = User.objects.filter(role='STUDENT').count()
        context['total_coordinators'] = User.objects.filter(role='COORDINATOR').count()
        context['total_clubs'] = Club.objects.filter(is_active=True).count()
        context['total_events'] = Event.objects.count()
        
        # Current month statistics
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        context['events_this_month'] = Event.objects.filter(
            created_at__gte=current_month_start
        ).count()
        
        context['registrations_this_month'] = EventRegistration.objects.filter(
            registration_date__gte=current_month_start
        ).count()
        
        context['new_users_this_month'] = User.objects.filter(
            date_joined__gte=current_month_start
        ).count()
        
        # Event status distribution
        context['event_status_data'] = list(
            Event.objects.values('status').annotate(count=Count('id'))
        )
        
        # Events by type
        context['event_type_data'] = list(
            Event.objects.values('event_type').annotate(count=Count('id'))
        )
        
        # Club category distribution
        context['club_category_data'] = list(
            Club.objects.filter(is_active=True).values('category').annotate(count=Count('id'))
        )
        
        # Recent activities
        context['recent_events'] = Event.objects.select_related('club').order_by('-created_at')[:5]
        context['recent_registrations'] = EventRegistration.objects.select_related(
            'event', 'user'
        ).order_by('-registration_date')[:10]
        
        # Top clubs by members
        context['top_clubs'] = Club.objects.filter(is_active=True).annotate(
            member_count=Count('members')
        ).order_by('-member_count')[:5]
        
        # Monthly event trend (last 6 months)
        monthly_data = []
        for i in range(5, -1, -1):
            month_date = now - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            if i > 0:
                next_month = now - timedelta(days=30*(i-1))
                month_end = next_month.replace(day=1)
            else:
                month_end = now
            
            event_count = Event.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            
            monthly_data.append({
                'month': month_start.strftime('%b %Y'),
                'count': event_count
            })
        
        context['monthly_event_data'] = json.dumps(monthly_data)
        
        return context


@login_required
def event_report(request, slug):
    event = get_object_or_404(Event, slug=slug)
    
    # Check permissions
    if not (request.user.is_admin() or 
            event.club.coordinator == request.user or
            event.organizer == request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    # Registration statistics
    total_registrations = EventRegistration.objects.filter(event=event).count()
    confirmed_registrations = EventRegistration.objects.filter(
        event=event, status='CONFIRMED'
    ).count()
    attended_count = EventRegistration.objects.filter(
        event=event, attended=True
    ).count()
    cancelled_count = EventRegistration.objects.filter(
        event=event, status='CANCELLED'
    ).count()
    
    # Attendance rate
    attendance_rate = (attended_count / confirmed_registrations * 100) if confirmed_registrations > 0 else 0
    
    # Feedback statistics
    feedback_stats = Feedback.objects.filter(event=event).aggregate(
        avg_rating=Avg('rating'),
        avg_organization=Avg('organization_rating'),
        avg_content=Avg('content_rating'),
        avg_venue=Avg('venue_rating'),
        total_feedback=Count('id')
    )
    
    # Department-wise participation (for students)
    department_stats = EventRegistration.objects.filter(
        event=event,
        user__role='STUDENT'
    ).values('user__department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Semester-wise participation
    semester_stats = EventRegistration.objects.filter(
        event=event,
        user__role='STUDENT'
    ).values('user__semester').annotate(
        count=Count('id')
    ).order_by('user__semester')
    
    context = {
        'event': event,
        'total_registrations': total_registrations,
        'confirmed_registrations': confirmed_registrations,
        'attended_count': attended_count,
        'cancelled_count': cancelled_count,
        'attendance_rate': attendance_rate,
        'feedback_stats': feedback_stats,
        'department_stats': department_stats,
        'semester_stats': semester_stats,
        'participants': EventRegistration.objects.filter(event=event).select_related('user'),
    }
    
    return render(request, 'reports/event_report.html', context)


@login_required
def club_report(request, slug):
    club = get_object_or_404(Club, slug=slug)
    
    # Check permissions
    if not (request.user.is_admin() or club.coordinator == request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    # Membership statistics
    total_members = ClubMembership.objects.filter(club=club, is_active=True).count()
    
    # Role distribution
    role_distribution = ClubMembership.objects.filter(
        club=club, is_active=True
    ).values('role').annotate(count=Count('id'))
    
    # Events organized
    total_events = Event.objects.filter(club=club).count()
    upcoming_events = Event.objects.filter(
        club=club,
        start_datetime__gte=timezone.now(),
        status='PUBLISHED'
    ).count()
    completed_events = Event.objects.filter(
        club=club,
        status='COMPLETED'
    ).count()
    
    # Total participation in club events
    total_participation = EventRegistration.objects.filter(
        event__club=club
    ).count()

    # Calculate participation rate
    participation_rate = (total_participation / total_members * 100) if total_members > 0 else 0
    
    # Average event rating
    avg_rating = Feedback.objects.filter(
        event__club=club
    ).aggregate(avg_rating=Avg('rating'))['avg_rating']
    
    # Department-wise member distribution
    department_stats = ClubMembership.objects.filter(
        club=club,
        is_active=True,
        user__role='STUDENT'
    ).values('user__department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent events
    recent_events = Event.objects.filter(club=club).order_by('-created_at')[:10]
    
    context = {
        'club': club,
        'total_members': total_members,
        'role_distribution': role_distribution,
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'completed_events': completed_events,
        'total_participation': total_participation,
        'participation_rate': participation_rate,
        'avg_rating': avg_rating,
        'department_stats': department_stats,
        'recent_events': recent_events,
        'members': ClubMembership.objects.filter(
            club=club, is_active=True
        ).select_related('user').order_by('-role', 'joined_date'),
    }
    
    return render(request, 'reports/club_report.html', context)


@login_required
def export_event_report(request, slug):
    """Export event report as CSV"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check permissions
    if not (request.user.is_admin() or 
            event.club.coordinator == request.user or
            event.organizer == request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    
    import csv
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{event.slug}_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'USN', 'Name', 'Email', 'Department', 'Semester', 
        'Registration Date', 'Status', 'Attended'
    ])
    
    registrations = EventRegistration.objects.filter(event=event).select_related('user')
    
    for reg in registrations:
        user = reg.user
        writer.writerow([
            user.usn or 'N/A',
            user.get_full_name(),
            user.email,
            user.department or 'N/A',
            user.semester or 'N/A',
            reg.registration_date.strftime('%Y-%m-%d %H:%M'),
            reg.status,
            'Yes' if reg.attended else 'No'
        ])

    # Add a separator for results
    writer.writerow([])
    writer.writerow(['Event Results'])
    writer.writerow(['Participant Name', 'Position', 'Prize', 'Remarks'])

    results = event.results.select_related('participant').order_by('position')
    for result in results:
        writer.writerow([
            result.participant.get_full_name(),
            result.position,
            result.prize,
            result.remarks
        ])
    
    return response


@login_required
def export_club_report(request, slug):
    """Export club report as CSV"""
    club = get_object_or_404(Club, slug=slug)

    # Check permissions
    if not (request.user.is_admin() or club.coordinator == request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    import csv

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{club.slug}_club_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Email', 'Role', 'Department', 'Semester', 'Joined Date'
    ])

    memberships = ClubMembership.objects.filter(club=club, is_active=True).select_related('user')

    for membership in memberships:
        user = membership.user
        writer.writerow([
            user.get_full_name(),
            user.email,
            membership.get_role_display(),
            user.department or 'N/A',
            user.semester or 'N/A',
            membership.joined_date.strftime('%Y-%m-%d %H:%M'),
        ])
    
    # Add a separator for other club statistics if needed
    writer.writerow([])
    writer.writerow(['Club Statistics'])
    writer.writerow(['Total Members', ClubMembership.objects.filter(club=club, is_active=True).count()])
    writer.writerow(['Total Events', Event.objects.filter(club=club).count()])
    # Add more statistics as needed

    return response