from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'organization_rating', 'content_rating', 
                  'venue_rating', 'comment', 'is_anonymous']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'organization_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'content_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'venue_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your experience...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'rating': 'Overall Rating',
            'organization_rating': 'Organization Quality',
            'content_rating': 'Content Quality',
            'venue_rating': 'Venue & Facilities',
            'is_anonymous': 'Submit Anonymously',
        }