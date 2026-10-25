from django.db import models
from django.conf import settings
from apps.events.models import Event

class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    
    # Detailed ratings
    organization_rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    content_rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    venue_rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True)
    
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedbacks'
        unique_together = ['event', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback for {self.event.title} by {self.user.get_full_name()}"