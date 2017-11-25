from django_cron import CronJobBase, Schedule
from accounts.helpers import send_test_email


class TestCronJob(CronJobBase):
    RUN_EVERY_MINS = 120

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'accounts.test_cron_job'

    def do(self):
        send_test_email()
