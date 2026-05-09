from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Sport, UserSport, Availability, EventGroup, Message

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Extends the default UserAdmin to include our custom bio and avatar fields
    so you don't break the password hashing UI in the admin panel.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Extras', {'fields': ('bio', 'avatar')}),
    )
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')

@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_players', 'max_players')
    search_fields = ('name',)

@admin.register(UserSport)
class UserSportAdmin(admin.ModelAdmin):
    list_display = ('user', 'sport', 'skill_level')
    list_filter = ('sport', 'skill_level')
    search_fields = ('user__username',)

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'is_available')
    list_filter = ('date', 'is_available')
    search_fields = ('user__username',)

@admin.register(EventGroup)
class EventGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'sport', 'date', 'status', 'captain', 'is_manual')
    list_filter = ('status', 'date', 'is_manual', 'sport')
    search_fields = ('captain__username', 'venue_name')
    filter_horizontal = ('players',) # Creates a sleek side-by-side widget for adding players

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'event', 'text_preview', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('sender__username', 'text')

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Message'
# Register your models here.
