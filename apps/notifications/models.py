from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = [
        ('EVENT', 'Event Notification'),
        ('CLUB', 'Club Notification'),
        ('GENERAL', 'General Notification'),
        ('REMINDER', 'Reminder'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_notifications'
    )
    
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='NotificationRecipient',
        related_name='received_notifications'
    )
    
    link = models.URLField(blank=True)
    send_email = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class NotificationRecipient(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_recipients'
        unique_together = ['notification', 'user']