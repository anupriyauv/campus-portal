from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Club(models.Model):
    CATEGORY_CHOICES = [
        ('TECHNICAL', 'Technical'),
        ('CULTURAL', 'Cultural'),
        ('SPORTS', 'Sports'),
        ('SOCIAL', 'Social Service'),
        ('ARTS', 'Arts & Creativity'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='club_covers/', blank=True, null=True)
    
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='coordinated_clubs',
        limit_choices_to={'role': 'COORDINATOR'}
    )
    
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ClubMembership',
        related_name='clubs'
    )
    
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    social_links = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clubs'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_member_count(self):
        return self.members.count()

class ClubMembership(models.Model):
    ROLE_CHOICES = [
        ('MEMBER', 'Member'),
        ('CORE_MEMBER', 'Core Member'),
        ('PRESIDENT', 'President'),
        ('VICE_PRESIDENT', 'Vice President'),
        ('SECRETARY', 'Secretary'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'club_memberships'
        unique_together = ['club', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.club.name} ({self.role})"