from django.shortcuts import render,get_object_or_404,redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Availability,EventGroup,Message,Sport,UserSport
from django.db.models import Count, F
from django.contrib import messages
from django.contrib.auth import login
from .forms import CustomUserCreationForm

def landing_page(request):
    """The public-facing homepage for unauthenticated users."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')
@login_required
def dashboard(request):
    """Main view where the user sees the ShowUpToday prompt and open matches."""
    today = timezone.now().date()
    availability = Availability.objects.filter(user=request.user, date=today).first()
    todays_event = EventGroup.objects.filter(players=request.user, date=today).first()
    
    # NEW: Find manual matches for today that aren't full yet
    open_matches = EventGroup.objects.filter(
        date=today,
        is_manual=True
    ).exclude(
        players=request.user # Don't show matches they are already in
    ).annotate(
        player_count=Count('players')
    ).filter(
        player_count__lt=F('sport__max_players') # Only show if there are empty slots
    )
    
    return render(request, 'core/dashboard.html', {
        'availability': availability,
        'todays_event': todays_event,
        'open_matches': open_matches
    })

@login_required
def join_match(request, event_id):
    """Endpoint for a user to join an open manual match."""
    today = timezone.now().date()
    
    # --- NEW: The Security Check ---
    is_available = Availability.objects.filter(user=request.user, date=today, is_available=True).exists()
    if not is_available:
        return redirect('dashboard')
    # -------------------------------
    if request.method == 'POST':
        today = timezone.now().date()
        
        # Enforce the "One match per day" rule here too!
        if EventGroup.objects.filter(players=request.user, date=today).exists():
            # In a real app we'd use toast notifications, but let's just redirect for the MVP
            return redirect('dashboard')
            
        event = get_object_or_404(EventGroup, id=event_id)
        
        # Double check it's not full just in case two people click at the exact same second
        if event.players.count() < event.sport.max_players:
            event.players.add(request.user)
            
            # Announce their arrival in the chat
            Message.objects.create(
                event=event,
                sender=request.user,
                text="Just joined the match! Ready to play."
            )
            
        # Teleport them into the event room
        return redirect('event_detail', event_id=event.id)

@login_required
def toggle_availability(request, status):
    """HTMX endpoint to handle the Yes/No click."""
    is_available = True if status == 'yes' else False
    today = timezone.now().date()
    
    # Update or create today's availability
    Availability.objects.update_or_create(
        user=request.user,
        date=today,
        defaults={'is_available': is_available}
    )
    
    # Return JUST a tiny snippet of HTML. HTMX will swap the buttons with this!
    if is_available:
        html = '''
        <div class="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg text-center shadow-sm transition-all animate-fade-in">
            <p class="font-bold text-lg">Awesome! 🚀</p>
            <p class="text-sm">We're looking for a match. Hang tight!</p>
        </div>
        '''
    else:
        html = '''
        <div class="p-4 bg-gray-100 border border-gray-300 text-gray-600 rounded-lg text-center shadow-sm transition-all animate-fade-in">
            <p class="font-bold">Maybe next time! 🛋️</p>
            <p class="text-sm text-gray-500">Rest up, we'll ask again tomorrow.</p>
        </div>
        '''
        
    response = HttpResponse()
    response['HX-Refresh'] = 'true'
    return response


@login_required
def event_detail(request, event_id):
    """The main staging area for the matched group."""
    event = get_object_or_404(EventGroup, id=event_id, players=request.user)
    return render(request, 'core/event_detail.html', {'event': event})

@login_required
def chat_messages(request, event_id):
    """HTMX endpoint to poll for new messages."""
    event = get_object_or_404(EventGroup, id=event_id, players=request.user)
    messages = event.messages.all().select_related('sender')
    return render(request, 'core/partials/chat_messages.html', {'messages': messages, 'event': event})

@login_required
def send_message(request, event_id):
    """HTMX endpoint to process a new message and return the updated chat."""
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            event = get_object_or_404(EventGroup, id=event_id, players=request.user)
            Message.objects.create(event=event, sender=request.user, text=text)
    
    # Return the updated message list instantly
    return chat_messages(request, event_id)
@login_required
def update_logistics(request, event_id):
    """HTMX endpoint for the captain to lock in the time and venue."""
    event = get_object_or_404(EventGroup, id=event_id, players=request.user)
    
    if request.method == 'POST' and request.user == event.captain:
        venue = request.POST.get('venue')
        time = request.POST.get('time')
        
        if venue and time:
            event.venue_name = venue
            event.time = time
            event.status = 'Confirmed'
            event.save()
            
            # Hackathon Polish: Auto-generate a chat message from the captain announcing it
            Message.objects.create(
                event=event, 
                sender=request.user, 
                text=f"🎯 Logistics Locked! We are playing at {venue} at {time}. See you there!"
            )

    # Return the updated logistics HTML block
    return render(request, 'core/partials/logistics.html', {'event': event})

from django.contrib import messages # Add this import at the top

@login_required
def create_manual_event(request):
    """Allows users to bypass matching and create their own event."""
    today = timezone.now().date()
    
    # --- NEW: The Security Check ---
    is_available = Availability.objects.filter(user=request.user, date=today, is_available=True).exists()
    if not is_available:
        return redirect('dashboard')
    if request.method == 'POST':
        sport_id = request.POST.get('sport')
        date = request.POST.get('date')
        
        if sport_id and date:
            # --- NEW HACKATHON RULE: One match per day ---
            if EventGroup.objects.filter(players=request.user, date=date).exists():
                sports = Sport.objects.all()
                return render(request, 'core/create_event.html', {
                    'sports': sports,
                    'error': f"You already have a match scheduled for {date}. Don't overtrain! One match per day."
                })
            # ---------------------------------------------

            sport = get_object_or_404(Sport, id=sport_id)
            
            # 1. Create the event immediately
            event = EventGroup.objects.create(
                sport=sport,
                date=date,
                status='Coordination', 
                captain=request.user,
                is_manual=True
            )
            
            # 2. Add the creator to the player roster
            event.players.add(request.user)
            
            # 3. Drop a welcome message in the chat
            Message.objects.create(
                event=event,
                sender=request.user,
                text="I just created this manual event. Let's get a game going!"
            )
            
            # 4. Teleport them straight to the command center
            return redirect('event_detail', event_id=event.id)
            
    # If GET request, show the form with available sports
    sports = Sport.objects.all()
    return render(request, 'core/create_event.html', {'sports': sports})
# Make sure UserSport is imported at the top!
# from .models import Sport, UserSport 

@login_required
def profile(request):
    """User profile to manage sports and skill levels."""
    if request.method == 'POST':
        sport_id = request.POST.get('sport')
        skill_level = request.POST.get('skill_level')
        
        if sport_id and skill_level:
            sport = get_object_or_404(Sport, id=sport_id)
            # Use get_or_create so they can't accidentally add Basketball twice
            UserSport.objects.get_or_create(
                user=request.user,
                sport=sport,
                defaults={'skill_level': skill_level}
            )
            return redirect('profile')
    
    # Get sports the user already plays
    user_sports = UserSport.objects.filter(user=request.user).select_related('sport')
    
    # Get sports they DON'T play yet (to populate the dropdown)
    available_sports = Sport.objects.exclude(id__in=user_sports.values_list('sport_id', flat=True))
    
    return render(request, 'core/profile.html', {
        'user_sports': user_sports,
        'available_sports': available_sports
    })

@login_required
def remove_sport(request, usersport_id):
    """Endpoint to delete a sport from the profile."""
    if request.method == 'POST':
        UserSport.objects.filter(id=usersport_id, user=request.user).delete()
    return redirect('profile')


def signup(request):
    """Handles user registration and logs them in immediately."""
    # If they are already logged in, send them away from the signup page
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log them in immediately after signing up
            return redirect('profile') # Send them to profile first so they add sports!
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'core/signup.html', {'form': form})
# Create your views here.
