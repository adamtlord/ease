from django_cron import CronJobBase, Schedule
from accounts.helpers import send_new_account_emails


class NewAccountsCronJob(CronJobBase):
    RUN_AT_TIMES = ['23:55']

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'accounts.new_accounts_cron_job'

    def do(self):
        return send_new_account_emails()
