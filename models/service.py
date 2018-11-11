from odoo import models, fields, api, tools
from odoo.osv import osv
from datetime import datetime
import time

class Contact(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        leads = []
        if 'email_from' in vals and vals['email_from']:
            leads = self.env['crm.lead'].search([('email_from','=',vals['email_from'])])
        if len(leads) > 0:
            lead = leads[0]
        else:
            lead = super(Contact, self).create(vals)
        return lead
        
class Enquiry(models.Model):
    _name = 'opencourse.enquiry'

    name = fields.Char(string="Enquirer name")
    email = fields.Char(string="Email")
    mobile = fields.Char(string="Mobile")
    subject = fields.Text(string="Subject")
    body = fields.Text(string="Body")
    support_mail = fields.Char(string="Support email")
    web_link = fields.Text(string="Website link")
    blog_link = fields.Text(string="Blog link")
    fb_link = fields.Text(string="Facebook link")
    tw_link = fields.Text(string="Twitter link")
    yt_link = fields.Text(string="Youtube link")
    gl_link = fields.Text(string="Google link")
    type = fields.Selection(
        [('contact', 'Contact'), ('teacher', 'Teacher'), ('collaborate', 'Collaborator')], default="contact")

    @api.model
    def create(self, vals):
        company = self.env.ref('base.main_company')
        vals["support_mail"] = company.email
        enquiry = super(Enquiry, self).create(vals)
        if enquiry.type == 'contact':
            self.env.ref(self._module + "." + "contact_enquiry_template").send_mail(enquiry.id, force_send=True)
        if enquiry.type == 'teacher':
            self.env.ref(self._module + "." + "teacher_enquiry_template").send_mail(enquiry.id, force_send=True)
        if enquiry.type == 'collaborate':
            self.env.ref(self._module + "." + "collaborate_enquiry_template").send_mail(enquiry.id, force_send=True)
        return enquiry


class NotificationService(osv.AbstractModel):
    _name = 'opencourse.notification_service'

    @api.model
    def sendSingleMail(self, params):
        email_from = 'info@vietinterview.com'
        email_to = params["email_to"]
        email_body = params["body"]
        email_subject = params["subject"]
        mail = self.env["mail.mail"].create({'email_from': email_from, 'body_html': email_body,
                                             'subject': email_subject, 'email_to': email_to})
        mail.send()
        return True

    @api.model
    def broadcastMail(self, params):
        email_from = 'info@vietinterview.com'
        email_cc = params["recipients"]
        email_body = params["body"]
        email_subject = params["subject"]
        mail = self.env["mail.mail"].create({'email_from': email_from, 'body_html': email_body,
                                             'subject': email_subject, 'email_to': email_from, 'email_cc': email_cc})
        mail.send()
        return True


class AccountService(osv.AbstractModel):
    _name = 'opencourse.account_service'

    @api.model
    def request_reset_password(self, params):
        login = params["login"]
        token = self.env['opencourse.reset_pass_token'].create({'login': login, 'cloud_id':self.id})
        self.env.ref(self._module +"."+"reset_password_template").send_mail(token.id,force_send=False)
        return {'success':True}

    @api.model
    def apply_reset_password(self,params):
        code = params['token']
        new_pass = params['new_pass']
        for token in self.env["opencourse.reset_pass_token"].search([('code','=',code)]):
            currentTime = int(round(time.time() * 1000))
            if token.date_expire < currentTime:
                return {'success':False,'message':'Token expired'}
            token.user_id.write({'password':new_pass})
            return {'success':True}