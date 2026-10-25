from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Event(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('WORKSHOP', 'Workshop'),
        ('SEMINAR', 'Seminar'),
        ('COMPETITION', 'Competition'),
        ('CONFERENCE', 'Conference'),
        ('CULTURAL', 'Cultural Event'),
        ('SPORTS', 'Sports Event'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    club = models.ForeignKey('clubs.Club', on_delete=models.CASCADE, related_name='events')
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_events'
    )
    
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    venue = models.CharField(max_length=200)
    
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    max_participants = models.IntegerField(blank=True, null=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='EventRegistration',
        related_name='registered_events'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'events'
        ordering = ['-start_datetime']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def is_registration_open(self):
        from django.utils import timezone
        return (
            self.status == 'PUBLISHED' and
            timezone.now() < self.registration_deadline and
            (self.max_participants is None or 
             self.participants.count() < self.max_participants)
        )
    
    def get_participant_count(self):
        return self.participants.filter(
            eventregistration__status='CONFIRMED'
        ).count()


class EventAnnouncement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Announcement for {self.event.title}: {self.title}"


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('ATTENDED', 'Attended'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    registration_date = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'event_registrations'
        unique_together = ['event', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"

class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='event_photos/')
    caption = models.CharField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'event_photos'
    
    def __str__(self):
        return f"Photo for {self.event.title}"

class EventResult(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='results')
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    position = models.IntegerField()
    prize = models.CharField(max_length=200, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'event_results'
        unique_together = ['event', 'participant']
        ordering = ['position']
    
    def __str__(self):
        return f"{self.participant.get_full_name()} - Position {self.position}"