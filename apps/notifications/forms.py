from django import forms
from .models import Notification
from apps.clubs.models import Club
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationForm(forms.ModelForm):
    recipient_type = forms.ChoiceField(
        choices=[
            ('all', 'All Users'),
            ('students', 'All Students'),
            ('coordinators', 'All Coordinators'),
            ('club', 'Club Members'),
            ('custom', 'Custom Users'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='all'
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select club if sending to club members'
    )
    
    custom_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '10'}),
        help_text='Select specific users (for custom option)'
    )
    
    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'link', 'send_email']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Notification Title'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Notification message...'
            }),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com (optional)'
            }),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BulkNotificationForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5})
    )
    
    send_to = forms.MultipleChoiceField(
        choices=[
            ('students', 'Students'),
            ('coordinators', 'Coordinators'),
            ('admins', 'Administrators'),
        ],
        widget=forms.CheckboxSelectMultiple(),
        required=True
    )
    
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )