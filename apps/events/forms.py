from django import forms
from .models import Event, EventPhoto, EventResult, EventAnnouncement
from apps.clubs.models import Club


class EventAnnouncementForm(forms.ModelForm):
    class Meta:
        model = EventAnnouncement
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }


class EventForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    
    end_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    
    registration_deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type', 'club', 'banner',
                  'venue', 'start_datetime', 'end_datetime', 'registration_deadline',
                  'max_participants', 'registration_fee', 'status', 'is_featured']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Event Title'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Event description...'
            }),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'club': forms.Select(attrs={'class': 'form-select'}),
            'banner': forms.FileInput(attrs={'class': 'form-control'}),
            'venue': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Venue'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter clubs based on user role
        if user:
            if user.is_coordinator():
                self.fields['club'].queryset = Club.objects.filter(coordinator=user)
            elif not user.is_admin():
                self.fields['club'].queryset = Club.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_datetime')
        end = cleaned_data.get('end_datetime')
        deadline = cleaned_data.get('registration_deadline')
        
        if start and end and start >= end:
            raise forms.ValidationError('End time must be after start time.')
        
        if deadline and start and deadline >= start:
            raise forms.ValidationError('Registration deadline must be before event start.')
        
        return cleaned_data


class EventPhotoForm(forms.ModelForm):
    class Meta:
        model = EventPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Photo caption'}),
        }


class EventResultForm(forms.ModelForm):
    class Meta:
        model = EventResult
        fields = ['participant', 'position', 'prize', 'remarks']
        widgets = {
            'participant': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.NumberInput(attrs={'class': 'form-control'}),
            'prize': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prize details'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }