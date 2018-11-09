# -*- coding: utf-8 -*-

from odoo import models, fields, api
from string import ascii_uppercase, digits
import random



class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    payment_request_id = fields.Many2one('opencourse.payment_request', string='Payment request')


class ActivationCode(models.Model):
    _name = 'opencourse.activation_code'

    payment_request_id = fields.Many2one('opencourse.payment_request', string='Payment request')
    code = fields.Char(string="Code")
    date_use = fields.Datetime(string="Date active")
    user_id = fields.Many2one('res.users', 'User')
    status = fields.Selection(
        [('initial', 'Initial'), ('open', 'Open'), ('used', 'Used')], default="initial")
    product_id = fields.Many2one('product.product', 'Subscription service')


    @api.model
    def create(self, vals):
        vals['code'] = ''.join(random.choice(ascii_uppercase + digits) for _ in range(8))
        request = super(ActivationCode, self).create(vals)
        return request


class PaymentRequest(models.Model):
    _name = 'opencourse.payment_request'

    name = fields.Char(string="Name")
    amount = fields.Float(string="Amount")
    ref = fields.Char(string="Ref")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    city = fields.Char(string="City")
    referal_code = fields.Char(string="Referal")
    support_mail = fields.Char(string="Support email")
    user_id = fields.Many2one('res.users', 'Learner')
    user_name = fields.Char(related="user_id.name", string="User name", readonly=True)
    referer_name = fields.Char(related="user_id.referal_name", string="Sales person", readonly=True)
    activation_code = fields.Char(related="activation_code_id.code", string="Activation code", readonly=True)
    activation_code_id = fields.Many2one('opencourse.activation_code', 'Activation code')
    address = fields.Text(string="Address")
    method = fields.Selection(
        [('home', 'Home'), ('counter', 'Counter'), ('wire', 'Bank Transfer')], default="counter")
    status = fields.Selection(
        [('open', 'Open'), ('rejected', 'Rejected'), ('processed', 'Processed')], default="open")
    date_payment = fields.Datetime(string="Date payment")

    @api.model
    def create(self, vals):
        company = self.env.ref('base.main_company')
        vals['ref'] = ''.join(random.choice(ascii_uppercase + digits) for _ in range(6))
        vals["support_mail"] = company.email
        request = super(PaymentRequest, self).create(vals)
        self.env.ref(self._module + "." + "payment_request_template").send_mail(request.id, force_send=True)
        return request

    @api.multi
    def confirm_payment(self):
        vals = {
            'staffId': self.user_id.id,
            'requestId': self.id,
            'account': {
                'login': self.user_id.email,
                'password': '123'
            }
        }
        print(vals)
        self.env['res.users'].confirm_payment(vals)

    @api.multi
    def dispense_code(self):
        vals = {
            'code': 'OPXW9Z9T',
            'userId': self.user_id.id
        }
        self.env['res.users'].dispense_code(vals)
        print(True)


