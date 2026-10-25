from django.contrib import admin
from .models import Notification, NotificationRecipient


class NotificationRecipientInline(admin.TabularInline):
    model = NotificationRecipient
    extra = 0
    raw_id_fields = ['user']
    fields = ['user', 'is_read', 'read_at']
    readonly_fields = ['read_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'sender', 'created_at', 'send_email', 'recipient_count']
    list_filter = ['notification_type', 'send_email', 'created_at']
    search_fields = ['title', 'message']
    raw_id_fields = ['sender']
    date_hierarchy = 'created_at'
    inlines = [NotificationRecipientInline]
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'message', 'notification_type', 'link')
        }),
        ('Settings', {
            'fields': ('sender', 'send_email')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def recipient_count(self, obj):
        count = obj.recipients.count()
        return format_html('<strong>{}</strong>', count)
    recipient_count.short_description = 'Recipients'


@admin.register(NotificationRecipient)
class NotificationRecipientAdmin(admin.ModelAdmin):
    list_display = ['notification', 'user', 'is_read', 'read_at']
    list_filter = ['is_read', 'read_at']
    search_fields = ['notification__title', 'user__email']
    raw_id_fields = ['notification', 'user']
    date_hierarchy = 'read_at'