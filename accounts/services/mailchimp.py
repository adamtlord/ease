from django.conf import settings
from mailchimp3 import MailChimp

ARRIVE_MASTER_LIST = '390301a3dc'

client = MailChimp(mc_api=settings.MAILCHIMP_API_KEY, mc_user=settings.MAILCHIMP_USERNAME)


def add_customer(customer, list_id=ARRIVE_MASTER_LIST):
    return client.lists.members.create(
        list_id, {
            'email_address': customer.email,
            'status': 'subscribed',
            'merge_fields': {
                'MMERGE4': '{} {}'.format(customer.first_name, customer.last_name),
                'MMERGE7': customer.home.fulladdress,
                'MMERGE16': customer.home.fulladdress,
            },
        }
    )
