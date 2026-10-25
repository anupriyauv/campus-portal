from django import forms
from .models import Club, ClubMembership
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['name', 'description', 'category', 'logo', 'cover_image', 
                  'email', 'website', 'coordinator']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Club Name'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your club...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'club@example.com'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'coordinator': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter coordinators
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['coordinator'].queryset = User.objects.filter(role='COORDINATOR')


class ClubMembershipForm(forms.ModelForm):
    class Meta:
        model = ClubMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
        }