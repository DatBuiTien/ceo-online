# -*- coding: utf-8 -*-

from odoo import models, fields, api
from string import ascii_uppercase, digits
import random
import time
from datetime import datetime
from odoo.exceptions import ValidationError


class Contact(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    mobile = fields.Char(string="Mobile")
    position = fields.Char(string="Position")
    intro = fields.Text(string="Introduction")
    fb_link = fields.Text(string="Facebook link")
    tw_link = fields.Text(string="Twitter link")
    ln_link = fields.Text(string="LinkedIn link")
    yt_link = fields.Text(string="Youtube link")
    gl_link = fields.Text(string="Google link")
    social_id = fields.Char(string="Social ID")
    hotline = fields.Char(string="Hotline")
    referal_code = fields.Char(string="Referal code")
    dob = fields.Datetime(string="Date of birth")
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('other', 'Other')])


class User(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    password = fields.Char(default='', invisible=False, copy=False)
    gender = fields.Selection(related='partner_id.gender', store=True)
    social_id = fields.Char(related="partner_id.social_id", string="Social ID", store=True)
    is_admin = fields.Boolean(default=False, string="Is admin")
    group_id = fields.Many2one('res.groups', string='Group')
    group_code = fields.Char(related="group_id.code", string="Code", readonl=True)
    group_name = fields.Char(related="group_id.name", string="Name", readonly=True)
    permission_id = fields.Many2one('opencourse.permission', string='Permission')
    referal_code = fields.Char(string="Referral code", related="partner_id.referal_code")
    street = fields.Char(related="partner_id.street", string="Address", inherited=True)
    mobile = fields.Char(related="partner_id.mobile", string="Mobile", inherited=True)
    intro = fields.Text(related="partner_id.intro", string="Intro", inherited=True)
    phone = fields.Char(related="partner_id.phone", string="Phone", inherited=True)
    position = fields.Char(related="partner_id.position", string="Position", inherited=True)
    ln_link = fields.Text(related="partner_id.ln_link", string="Linked", inherited=True)
    fb_link = fields.Text(related="partner_id.fb_link", string="Facebook", inherited=True)
    tw_link = fields.Text(related="partner_id.tw_link", string="Twitter", inherited=True)
    dob = fields.Datetime(related="partner_id.dob", string="Date of birth", inherited=True)
    banned = fields.Boolean(default=False, string="Is banned")
    referer_id = fields.Many2one('res.users', string='Referer')
    supervisor_id = fields.Many2one('res.users', string='Supervisor')
    subscription_id = fields.Many2one('opencourse.subscription', string='Subscription')
    date_start = fields.Datetime(related="subscription_id.date_start", string="Date start")
    date_expire = fields.Datetime(related="subscription_id.date_expire", string="Date expire")
    role = fields.Selection(
        [('staff', 'Staff'), ('learner', 'Learner'), ('teacher', 'Teacher'), ('sales', 'Sales')])
    permission_name = fields.Char(related="permission_id.name", string="Permission Name")
    supervisor_name = fields.Char(related="supervisor_id.name", string="Supervisor Name")
    course_member_ids = fields.One2many('opencourse.course_member', 'user_id', string='Course members')
    referal_name = fields.Char(related="referer_id.name", string="Referal Name", readonly=True)
    debit = fields.Monetary(related="partner_id.debit", string="Balance", readonly=True)
    payment_request_ids = fields.One2many('opencourse.payment_request', 'user_id', string='Payment request')
    activation_code_ids = fields.One2many('opencourse.activation_code', 'user_id', string='Activation code')

    @api.model
    def create(self, vals):
        if "login" not in vals:
            vals["login"] = vals["email"]
        vals["login"] = vals["login"].lower()
        if 'referal_code' not in vals:
            vals['referal_code'] = vals['code'] = ''.join(random.choice(ascii_uppercase + digits) for _ in range(8))
        user = super(User, self.with_context({"no_reset_password": True})).create(vals)
        if user.role == 'learner':
            subscription = self.env["opencourse.subscription"].create({})
            user.write({'subscription_id': subscription.id})
        acc_type = self.env["account.account.type"].create({"name": vals["login"], "type": "payable"})
        account = self.env['account.account'].create(
            {"name": vals["name"], "code": vals["login"], "user_type_id": acc_type.id, "reconcile": True})
        user.partner_id.write({'property_account_payable_id': account.id})
        user.partner_id.write({'property_account_receivable_id': account.id})
        return user

    @api.multi
    def check_email_user(self, vals):
        if vals['email'] and vals['email'] != '':
            check_email = self.search([('email', '=', vals['email'])])
            if check_email:
                return {'success': False, 'message': 'Email đã tồn tại trên hệ thống'}
        return {'success': True}

    @api.model
    def register(self, params):
        self = self.sudo()
        user = params["user"]
        if self.env["res.users"].search([("login", "=", user["login"])]):
            return {"success": False, "code": "USER_EXIST", "message": "Username exist"}
        user = super(User, self).with_context({"no_reset_password": True}).create(user)
        return {"success": True, "user_id": user.id}

    @api.one
    def extends_subscription(self, service):
        print(service)
        result = self.subscription_id.extend(service)
        if result:
            self.env['opencourse.subscription_history'].create({'subscription_id': self.subscription_id.id,
                                                                'action_date': datetime.now(),
                                                                'service_id': service.id,
                                                                'user_id': self.id,
                                                                'days': service.days,
                                                                'price': service.price,
                                                                'status': 'success',
                                                                'action': 'extend'})
        return True

    @api.model
    def dispense_code(self, params):
        code = params["code"]
        userId = params["userId"]
        for user in self.env['res.users'].browse(userId):
            for activation_code in self.env['opencourse.activation_code'].search([('code', '=', code)]):
                if activation_code.status == 'used':
                    return {'status': False, 'error': 'ACTIVATION_CODE_USED', 'message': 'Mã đã được sử dụng.'}
                user.extends_subscription(activation_code.product_id)
                activation_code.write({'status': 'used', 'date_use': fields.Datetime.now()})
                return {'status': True, 'activation_code': activation_code.read(),
                        'subscription': user.subscription_id.read()}

    @api.model
    def confirm_payment(self, params):
        staffId = params["staffId"]
        requestId = +params["requestId"]
        account = params["account"]
        print(params)
        for staff in self.env['res.users'].browse(staffId):
            for request in self.env['opencourse.payment_request'].browse(requestId):
                learner_id = request.user_id
                payment = self.env['account.payment'].create({'payment_type': 'inbound',
                                                              'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                                              'partner_type': 'customer',
                                                              'partner_id': learner_id.partner_id.id,
                                                              'amount': request.amount,
                                                              'journal_id': self.env.ref(self._module + "." + 'cash_journal').id})

                payment.post()

                activation_code = self.env['opencourse.activation_code'].create({'payment_request_id': requestId,
                                                                                 'product_id': request.product_id.id,
                                                                                 'user_id': request.user_id.id,
                                                                                 'status': 'open'})
                request.write({'status': 'confirmed', 'activation_code_id': activation_code.id,
                               'date_payment': fields.Datetime.now()})
                if not learner_id.referer_id and request.referal_code:
                    referer = self.env['res.users'].search(
                        [('role', '=', 'staff'), ('referal_code', '=', request.referal_code)])
                    if referer:
                        learner_id.write({'referer_id': referer.id})
                if account:

                    self.env.ref(self._module + "." + "registration_and_activation_code_template").with_context(
                        {"password": account["password"], "login": account["login"]}).send_mail(activation_code.id,
                                                                                                force_send=True)
                else:
                    self.env.ref(self._module + "." + "activation_code_template").send_mail(activation_code.id,
                                                                                            force_send=True)
                return {"success": True, "code": activation_code.read()}

    @api.model
    def change_password(self, params):
        userId = +params["userId"]
        old_passwd = params["old_pass"]
        new_passwd = params["new_pass"]
        self.check(self._cr.dbname, userId, old_passwd)
        if new_passwd:
            for user in self.env['res.users'].browse(userId):
                return user.write({'password': new_passwd})
        raise ValidationError(_("Setting empty passwords is not allowed for security reasons!"))


class ResetPassToken(models.Model):
    _name = 'opencourse.reset_pass_token'

    code = fields.Char(string='Token')
    date_expire = fields.Float(string='Time in millseconds')
    login = fields.Char(string='Login')
    email = fields.Char(string='Email')
    reset_link = fields.Text(string="Reset link")
    user_id = fields.Many2one('res.users')

    @api.model
    def create(self, vals):
        cr, uid, context = self.env.args
        if "account" in context:
            account = context["account"]
            for user in self.env['res.users'].search([("login", "=", vals["login"])]):
                vals["email"] = user.email
                vals["user_id"] = user.id
            vals['code'] = ''.join(random.choice(ascii_uppercase + digits) for _ in range(24))
            vals["date_expire"] = int(round(time.time() * 1000)) + 1000 * 60 * 60 * 24
            vals["reset_link"] = '%s/auth/reset-pass/%s' % (account["domain"], vals['code'])
        return super(ResetPassToken, self).create(vals)


class Permission(models.Model):
    _name = 'opencourse.permission'

    name = fields.Char(string="Name")
    menu_access = fields.Text(string="Menu access")
    user_ids = fields.One2many('res.users', 'permission_id', string='Users')
    user_group_id = fields.Many2one('res.groups', string='Group')
    user_group_name = fields.Char(related="user_group_id.name", string="Group Name")
    user_count = fields.Integer(compute='_compute_user_count', string='User count')

    def _compute_user_count(self):
        for perm in self:
            perm.user_count = len(perm.user_ids)
