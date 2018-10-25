# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CourseLog(models.Model):
    _name = 'opencourse.course_log'

    res_model = fields.Char('Resource Model', help="The database object this attachment will be attached to.")
    res_id = fields.Integer('Resource ID', help="The record id this is attached to.")
    start = fields.Datetime('Start time')
    note = fields.Text('Note')
    code = fields.Char('Code')
    attachment_id = fields.Many2one('ir.attachment', string="Attachment")
    attachment_url = fields.Char(related="attachment_id.url", string="Attachment URL")
    user_id = fields.Many2one('res.users', related='member_id.user_id', string="Target user")
    member_id = fields.Many2one('opencourse.course_member', string="Target member")
    course_id = fields.Many2one('opencourse.course', related='member_id.course_id', string="Course")


class UserLog(models.Model):
    _name = 'opencourse.user_log'

    res_model = fields.Char('Resource Model', help="The database object this attachment will be attached to.")
    res_id = fields.Integer('Resource ID', help="The record id this is attached to.")
    start = fields.Datetime('Start time')
    note = fields.Text('Note')
    code = fields.Char('Code')
    user_id = fields.Many2one('res.users', string="Target user")


class WebLog(models.Model):
    _name = 'opencourse.web_log'

    res_model = fields.Char('Resource Model', help="The database object this attachment will be attached to.")
    res_id = fields.Integer('Resource ID', help="The record id this is attached to.")
    start = fields.Datetime('Start time')
    note = fields.Text('Note')
    code = fields.Char('Code')

    @api.model
    def create(self, vals):
        log = super(WebLog, self).create(vals)
        if log.res_model == 'opencourse.course' and log.code == 'view':
            for course in self.env['opencourse.course'].browse([log.res_id]):
                course.write({'view_count': course.view_count + 1})
        return log
