# -*- coding: utf-8 -*-

from odoo import models, fields, api
import time
from datetime import datetime
from datetime import timedelta


class Subscription(models.Model):
    _name = 'opencourse.subscription'

    date_expire = fields.Datetime(string="Date of expire")
    date_start = fields.Datetime(string="Date of start", default=fields.Datetime.now())
    user_id = fields.Many2one('res.users', string='User')

    @api.multi
    def extend(self, service):
        if self.date_expire:
            date_expire = datetime.strptime(self.date_expire, "%Y-%m-%d %H:%M:%S")
            if date_expire <= datetime.now():
                date_start = datetime.now()
                date_expire = datetime.now() + timedelta(days=service.days)
                self.write({'date_start': date_start, 'date_expire': date_expire})
            else:
                date_expire = date_expire + timedelta(days=service.days)
                self.write({'date_expire': date_expire})
        else:
            date_start = datetime.now()
            date_expire = datetime.now() + timedelta(days=service.days)
            self.write({'date_start': date_start, 'date_expire': date_expire})
        return True


class SubscriptionHistory(models.Model):
    _name = 'opencourse.subscription_history'

    subscription_id = fields.Many2one('opencourse.subscription', string='Subscription')
    action_date = fields.Datetime(string="Date of expire")
    user_id = fields.Many2one('res.users', string='Learneruser')
    service_id = fields.Many2one('product.product', string='Service')
    price = fields.Float(string="Service price")
    status = fields.Char(string="Status")
    action = fields.Char(string="Action")
    days = fields.Integer(string="Days of subscription")


class Product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    days = fields.Integer(string="Days of subscription")