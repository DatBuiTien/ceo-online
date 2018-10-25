from odoo import models, fields, api, tools
from odoo.osv import osv
from datetime import datetime


class Bootstrap(osv.AbstractModel):
    _name = 'opencourse.bootstrap'

    @api.model
    def install(self):
        # Set up cron task
        now = datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=1, microsecond=0)
        next_call = '%d-%d-%d %d:%d:%d' % (
            tomorrow.year, tomorrow.month, tomorrow.day, tomorrow.hour, tomorrow.minute, tomorrow.second)
        self.env['ir.cron'].create(
            {'name': 'HOURLY_TASK', 'interval_number': 1, 'interval_type': 'hours', 'numbercall': -1,
             'model': 'opencourse.cron_task', 'function': 'runHourly', 'nextcall': next_call})


class CronTask(osv.AbstractModel):
    _name = 'opencourse.cron_task'

    @api.model
    def runDaily(self):
        return True

    @api.model
    def runHourly(self):
        return True

    @api.model
    def runWeekly(self):
        return True

    @api.model
    def runMonthly(self):
        return True
