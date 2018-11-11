# -*- coding: utf-8 -*-

from odoo import models, fields, api
from string import ascii_uppercase, digits
import random
import time
from datetime import datetime


class Company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    ln_link = fields.Text(related="partner_id.ln_link", string="Linked", store=True)
    fb_link = fields.Text(related="partner_id.fb_link", string="Facebook", store=True)
    tw_link = fields.Text(related="partner_id.tw_link", string="Twitter", store=True)
    gl_link = fields.Text(related="partner_id.gl_link", string="Google", store=True)
    yt_link = fields.Text(related="partner_id.yt_link", string="Youtube", store=True)
    mobile = fields.Char(related="partner_id.mobile", string="Mobile", store=True)
    hotline = fields.Char(related="partner_id.hotline", string="Hotline", store=True)
    head_quarter = fields.Text(string="Headquarter")
    commission_rate = fields.Float(string="Commission rate")