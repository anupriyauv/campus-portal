from django.contrib import admin
from .models import Event, EventRegistration, EventPhoto, EventResult

class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    raw_id_fields = ['user']

class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    extra = 0
    readonly_fields = ['uploaded_by']

class EventResultInline(admin.TabularInline):
    model = EventResult
    extra = 0
    raw_id_fields = ['participant']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'organizer', 'event_type', 'status', 'start_datetime', 'is_featured')
    list_filter = ('event_type', 'status', 'is_featured', 'club')
    search_fields = ('title', 'description', 'club__name', 'organizer__username')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['club', 'organizer']
    inlines = [EventRegistrationInline, EventPhotoInline, EventResultInline]
    date_hierarchy = 'start_datetime'
    ordering = ('-start_datetime',)

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'status', 'registration_date', 'attended')
    list_filter = ('status', 'attended', 'event')
    search_fields = ('event__title', 'user__username')
    raw_id_fields = ['event', 'user']
    date_hierarchy = 'registration_date'

@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ('event', 'caption', 'uploaded_by', 'uploaded_at')
    list_filter = ('event', 'uploaded_by')
    search_fields = ('event__title', 'caption')
    raw_id_fields = ['event', 'uploaded_by']
    date_hierarchy = 'uploaded_at'

@admin.register(EventResult)
class EventResultAdmin(admin.ModelAdmin):
    list_display = ('event', 'participant', 'position', 'prize')
    list_filter = ('event', 'position')
    search_fields = ('event__title', 'participant__username', 'prize')
    raw_id_fields = ['event', 'participant']
    ordering = ('event__title', 'position')