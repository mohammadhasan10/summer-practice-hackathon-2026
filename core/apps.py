from django.apps import AppConfig

from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command
import os
class CoreConfig(AppConfig):
    name = 'core'
    def ready(self):
        # This check prevents the scheduler from running twice in development mode
        if os.environ.get('RUN_MAIN'):
            from apscheduler.schedulers.background import BackgroundScheduler
            from django.core.management import call_command

            def run_algorithm():
                print("Running the matching algorithm...")
                call_command('run_matching')

            # Initialize the background timer
            scheduler = BackgroundScheduler()
            
            # For your hackathon testing, this runs every 1 minute.
            # (To run once a day, you would change this to: 'cron', hour=12, minute=0)
            scheduler.add_job(run_algorithm, 'interval', minutes=1)
            
            scheduler.start()


