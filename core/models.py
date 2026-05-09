from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """Custom user model for quick profile iteration."""
    bio = models.TextField(max_length=500, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    def __str__(self):
        return self.username

class Sport(models.Model):
    """e.g., Football, Tennis. Defines matching constraints."""
    name = models.CharField(max_length=100, unique=True)
    min_players = models.PositiveIntegerField(default=2)
    max_players = models.PositiveIntegerField(default=14)
    
    def __str__(self):
        return f"{self.name} ({self.min_players}-{self.max_players} players)"

class UserSport(models.Model):
    """Through model to track which sports a user plays and their skill level."""
    SKILL_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sports')
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    skill_level = models.CharField(max_length=20, choices=SKILL_CHOICES, default='Intermediate')

    class Meta:
        unique_together = ('user', 'sport')

class Availability(models.Model):
    """The 'ShowUpToday' declaration."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField(default=timezone.now)
    is_available = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'date') # One declaration per day

    def __str__(self):
        return f"{self.user.username} - {self.date} - {'Yes' if self.is_available else 'No'}"

class EventGroup(models.Model):
    """The auto-matched or manually created event."""
    STATUS_CHOICES = [
        ('Draft', 'Draft (Matching)'),
        ('Coordination', 'Coordination (Captain Assigned)'),
        ('Confirmed', 'Confirmed (Ready to Play)'),
    ]
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Auto-assigned captain
    captain = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='captained_events')
    players = models.ManyToManyField(User, related_name='events')
    
    # Logistics
    venue_name = models.CharField(max_length=255, blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    
    # Flag to differentiate auto-matched vs manual events
    is_manual = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sport.name} on {self.date} (Status: {self.status})"

class Message(models.Model):
    """For the group chat coordination."""
    event = models.ForeignKey(EventGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} in {self.event.id}: {self.text[:20]}"
# Create your models here.
