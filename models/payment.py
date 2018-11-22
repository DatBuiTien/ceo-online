# -*- coding: utf-8 -*-

from odoo import models, fields, api
from string import ascii_uppercase, digits
import random
import datetime
import string


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    payment_request_id = fields.Many2one('opencourse.payment_request', string='Payment request')


class ActivationCode(models.Model):
    _name = 'opencourse.activation_code'

    payment_request_id = fields.Many2one('opencourse.payment_request', string='Payment request')
    code = fields.Char(string="Code")
    date_use = fields.Datetime(string="Date active")
    product_id = fields.Many2one('product.product', 'Subscription service')
    service_name = fields.Char(related="product_id.name", string="Name")
    service_length = fields.Integer(related="product_id.days", string="Length")

    user_id = fields.Many2one('res.users', 'User')
    status = fields.Selection(
        [('initial', 'Initial'), ('open', 'Open'), ('used', 'Used')], default="initial")

    @api.model
    def create(self, vals):
        vals['code'] = ''.join(random.choice(ascii_uppercase + digits) for _ in range(8))
        request = super(ActivationCode, self).create(vals)
        return request


class PaymentRequest(models.Model):
    _name = 'opencourse.payment_request'

    name = fields.Char(string="Name")
    amount = fields.Float(string="Amount")
    ref = fields.Char(string="Code bill")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    city = fields.Char(string="City")
    referal_code = fields.Char(string="Referral code")
    support_mail = fields.Char(string="Support email")
    user_id = fields.Many2one('res.users', 'Learner')
    user_name = fields.Char(related="user_id.name", string="User name", readonly=True)
    referer_name = fields.Char(related="user_id.referal_name", string="Sales person", readonly=True)
    activation_code = fields.Char(related="activation_code_id.code", string="Activation code", readonly=True)
    activation_code_id = fields.Many2one('opencourse.activation_code', 'Activation code')
    product_id = fields.Many2one('product.product', 'Subscription service')
    service_name = fields.Char(related="product_id.name", string="Service name", readonly=True)
    service_price = fields.Float(related="product_id.list_price", string="Service price", readonly=True)
    service_length = fields.Integer(related="product_id.days", string="Service duration", readonly=True)

    address = fields.Text(string="Address")
    method = fields.Selection(
        [('home', 'Home'), ('counter', 'Counter'), ('wire', 'Bank Transfer')], default="counter")
    status = fields.Selection(
        [('open', 'Open'), ('rejected', 'Rejected'), ('confirmed', 'Confirmed')], default="open")
    date_payment = fields.Datetime(string="Date payment", default=datetime.datetime.now())

    @api.model
    def create(self, vals):
        company = self.env.ref('base.main_company')
        vals['ref'] = ''.join(random.choice(ascii_uppercase + digits) for _ in range(6))
        vals["support_mail"] = company.email
        request = super(PaymentRequest, self).create(vals)
        self.env.ref(self._module + "." + "payment_request_template").send_mail(request.id, force_send=True)
        return request

    @api.multi
    def check_email_payment(self, vals):
        print(vals)
        if vals['email'] and vals['email'] != '':
            payment = self.env['res.users'].sudo().search([('email', '=', vals['email'])])
            if payment:
                return {'success': False, 'message': 'Email đã tồn tại trên hệ thống. Bạn đã có tài khoản, vui lòng đăng nhập để thực hiện tiếp'}
            return {'success': True}

    @api.multi
    def reject(self, vals):
        request_id = vals['RequestId']
        request = self.env['opencourse.payment_request'].browse(request_id)
        request.status = 'rejected'
        self.env.ref(self._module + "." + "reject_payment_template").send_mail(request.id, force_send=True)
        return request

    @api.model
    def upload(self, vals):
        vals = {
            'name': 'Tuấn',
            'login': 'oktung123@gmail.com',
            'email': 'oktung123@gmail.com',
            'phone': '0303988834',
            'address': 'Hồ Tùng Mậu',
            'city': 'Hà Nội',
            'referal_code': '',
            'method': 'counter',
            'amount': 200000
        }
        if self.env['res.users'].search([('login', '=', vals['login'])]):
            return {'success': False, 'message': 'Account exist !'}
        user_vals = vals
        user_vals.update({
            'password': ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8)),
            'role': 'learner'
        })
        print(user_vals['password'])
        user = self.env['res.users'].create(user_vals)
        payment_vals = vals
        payment_vals.update({
            'user_id': user.id
        })



    @api.multi
    def confirm_payment(self):
        vals = {
            'staffId': self.user_id.id,
            'requestId': self.id,
            'account': {
                'login': self.user_id.email,
                'password': ''.join(random.choice(ascii_uppercase + digits) for _ in range(6))
            },
            'productId': 1
        }
        print(vals)
        self.env['res.users'].confirm_payment(vals)

    @api.multi
    def dispense_code(self):
        vals = {
            'code': 'DXEMA7JM',
            'userId': self.user_id.id
        }
        self.env['res.users'].dispense_code(vals)
        print(True)




