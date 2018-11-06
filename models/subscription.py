# -*- coding: utf-8 -*-

from odoo import models, fields, api
import time
from datetime import datetime
from datetime import timedelta


class Subscription(models.Model):
    _name = 'opencourse.subscription'

    # date_expire = fields.Datetime(string="Date of expire")
    date_start = fields.Datetime(string="Date of start", default=fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='User')

    @api.multi
    def extend(self):
        date_start = datetime.now()
        self.write({'date_start': date_start})
        return True


class SubscriptionHistory(models.Model):
    _name = 'opencourse.subscription_history'

    subscription_id = fields.Many2one('opencourse.subscription', string='Subscription')
    action_date = fields.Datetime(string="Date of expire")
    user_id = fields.Many2one('res.users', string='Learneruser')
    price = fields.Float(string="Service price")
    status = fields.Char(string="Status")
    action = fields.Char(string="Action")

class Product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    days = fields.Integer(string="Days of subscription")