from django.core.management.base import BaseCommand
from accounts.models import Customer
from rides.models import Destination


class Command(BaseCommand):
    help = 'Moves contents of residence instructions field to customer.home.notes'

    def handle(self, *args, **options):
        homes = Destination.objects.filter(home=True)
        customers_with_homes = [home.customer for home in homes]
        self.stdout.write('Found {} customers with homes'.format(len(customers_with_homes)))
        for customer in customers_with_homes:
            self.stdout.write('Customer {}'.format(customer))
            new_notes = ''
            residence_instructions = customer.residence_instructions
            home = customer.home
            home_notes = home.notes or ''
            instructions_to_append = ''
            if residence_instructions:
                instructions_to_append = ', {}'.format(residence_instructions)
            else:
                self.stdout.write(self.style.NOTICE('No residence instructions for {}'.format(customer)))
            new_notes = '{}{}'.format(home_notes, instructions_to_append)
            self.stdout.write('Instructions: {}'.format(residence_instructions))
            self.stdout.write('Notes: {}'.format(home_notes))
            self.stdout.write('New notes: {}'.format(new_notes))
            self.stdout.write('--')
            home.notes = new_notes
            home.save()
            self.stdout.write(self.style.SUCCESS('Migrated notes for {} <{}>'.format(customer, customer.id)))
