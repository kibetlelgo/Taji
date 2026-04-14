from django.core.management.base import BaseCommand
from core.models import Cycle


class Command(BaseCommand):
    help = 'Initialize the first 60-day cycle if none exists'

    def handle(self, *args, **kwargs):
        if Cycle.objects.exists():
            self.stdout.write('Cycle already exists.')
        else:
            cycle = Cycle.create_next()
            self.stdout.write(self.style.SUCCESS(
                f'Created Cycle 1: {cycle.start_date} to {cycle.end_date}'
            ))
