from django.core.management.base import BaseCommand
from accounts.models import Customer


class Command(BaseCommand):
    help = 'Fetches and sets timezone information for all customers'

    def handle(self, *args, **options):
        customers = Customer.objects.filter(timezone__isnull=True)
        self.stdout.write('Found {} customers'.format(customers.count()))
        for customer in customers:
            home = customer.destination_set.filter(home=True).first()
            if home:
                if not (home.latitude and home.longitude):
                    try:
                        home.set_ltlng()
                    except Exception as ex:
                        self.stdout.write(self.style.NOTICE('Could not set ltlng for {} home: {} <{}>'.format(customer, customer.id, ex)))
                try:
                    home.set_timezone()
                except Exception as ex:
                    self.stdout.write(self.style.NOTICE('Could not set timezone for {}: {} <{}>'.format(customer, customer.id, ex)))
            else:
                self.stdout.write(self.style.NOTICE('{} <{}> does not have a home address!'.format(customer, customer.id)))

            self.stdout.write(self.style.SUCCESS('Successfully set timezone for {} <{}>'.format(customer, customer.id)))
