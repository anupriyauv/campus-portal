from django.contrib import admin
from django.contrib.admin import AdminSite


class CampusAdminSite(AdminSite):
    site_header = 'Campus Event Portal Administration'
    site_title = 'Campus Portal Admin'
    index_title = 'Welcome to Campus Event Portal Administration'
    
    def each_context(self, request):
        context = super().each_context(request)
        
        # Add custom context
        from apps.events.models import Event
        from apps.clubs.models import Club
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        context['total_users'] = User.objects.count()
        context['total_clubs'] = Club.objects.filter(is_active=True).count()
        context['total_events'] = Event.objects.count()
        context['active_events'] = Event.objects.filter(status='PUBLISHED').count()
        
        return context


# Create custom admin site instance
campus_admin_site = CampusAdminSite(name='campus_admin')