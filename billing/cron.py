from dateutil.relativedelta import relativedelta

from django.utils import timezone

from django_cron import CronJobBase, Schedule

from billing.models import Subscription
from billing.utils import debit_customer_balance


class SubscriptionCronJob(CronJobBase):
    RUN_AT_TIMES = ['23:50']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'billing.subscription_cron_job'

    def do(self):
        today = timezone.now().date()
        subscriptions_due = Subscription.objects.filter(next_billed_date=today).prefetch_related('customer')
        for subscription in subscriptions_due:
            success = debit_customer_balance(subscription.customer)
            if success:
                subscription.last_billed_date = today
                subscription.next_billed_date = today + relativedelta(months=1)
                subscription.save()
            else:
                continue
