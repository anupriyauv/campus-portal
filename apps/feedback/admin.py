from django.contrib import admin
from django.db.models import Avg
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rating', 'organization_rating', 'content_rating', 'venue_rating', 'is_anonymous', 'created_at']
    list_filter = ['rating', 'is_anonymous', 'created_at', 'event']
    search_fields = ['event__title', 'user__email', 'comment']
    raw_id_fields = ['event', 'user']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event & User', {
            'fields': ('event', 'user', 'is_anonymous')
        }),
        ('Ratings', {
            'fields': ('rating', 'organization_rating', 'content_rating', 'venue_rating')
        }),
        ('Feedback', {
            'fields': ('comment',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            response.context_data['avg_rating'] = qs.aggregate(Avg('rating'))['rating__avg']
        except:
            pass
        return response