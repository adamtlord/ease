from django.core.management.base import BaseCommand
from rides.models import Destination


class Command(BaseCommand):
    help = 'Fetches and sets timezone information for all destinations (idempotent)'

    def handle(self, *args, **options):
        destinations = Destination.objects.filter(timezone__isnull=True)
        self.stdout.write('Found {} destinations'.format(destinations.count()))
        for destination in destinations:
            if not (destination.latitude and destination.longitude):
                try:
                    destination.set_ltlng()
                except Exception as ex:
                    self.stdout.write(self.style.NOTICE('Could not set ltlng for {} home: {} <{}>'.format(destination, destination.id, ex)))
            try:
                destination.set_timezone()
            except Exception as ex:
                self.stdout.write(self.style.NOTICE('Could not set timezone for {}: {} <{}>'.format(destination, destination.id, ex)))

            self.stdout.write(self.style.SUCCESS('Successfully set timezone for {} <{}>'.format(destination, destination.id)))
