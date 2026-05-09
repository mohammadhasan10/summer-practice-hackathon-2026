import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Availability, UserSport, EventGroup

class Command(BaseCommand):
    help = 'Runs the smart matching algorithm for today to group available players.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(f"Starting matching engine for {today}...")
        
        already_matched_users = EventGroup.objects.filter(date=today).values_list('players', flat=True)
        
        available_users = Availability.objects.filter(
            date=today, 
            is_available=True
        ).exclude(user__id__in=already_matched_users).values_list('user', flat=True)

        if not available_users:
            self.stdout.write(self.style.WARNING("No available unmatched users found for today."))
            return

        user_sports = UserSport.objects.filter(user__id__in=available_users).select_related('sport', 'user')
        
        sport_queues = {}
        for us in user_sports:
            if us.sport not in sport_queues:
                sport_queues[us.sport] = []
            sport_queues[us.sport].append(us.user)

        events_created = 0
        
        # NEW: Keep an active memory of who gets matched during this exact run
        matched_in_this_run = set() 

        for sport, players in sport_queues.items():
            random.shuffle(players)
            
            # NEW: Filter out anyone who got snatched up by a previous sport in this loop
            available_for_this_sport = [p for p in players if p.id not in matched_in_this_run]
            
            for i in range(0, len(available_for_this_sport), sport.max_players):
                chunk = available_for_this_sport[i:i + sport.max_players]
                
                if len(chunk) >= sport.min_players:
                    captain = random.choice(chunk)
                    
                    event = EventGroup.objects.create(
                        sport=sport,
                        date=today,
                        status='Coordination',
                        captain=captain,
                        is_manual=False
                    )
                    event.players.set(chunk)
                    events_created += 1
                    
                    # NEW: Add these players to the temporary blacklist so they don't get double-booked
                    for p in chunk:
                        matched_in_this_run.add(p.id)
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"Match Found! {sport.name} event created with {len(chunk)} players. Captain: {captain.username}"
                    ))
                else:
                    self.stdout.write(self.style.NOTICE(
                        f"Not enough players for {sport.name}. Have {len(chunk)}, need {sport.min_players}."
                    ))

        self.stdout.write(self.style.SUCCESS(f"Matching complete. {events_created} events generated."))