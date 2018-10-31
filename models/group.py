# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Group(models.Model):
    _name = 'res.groups'
    _inherit = 'res.groups'

    parent_id = fields.Many2one('res.groups', string='Parent group')
    child_ids = fields.One2many('res.groups', 'parent_id', string='Child groups')
    order = fields.Integer(string="Order", default=0)
    code = fields.Char(string="Code")
    icon = fields.Char(string="Icon")
    logo_url = fields.Char(string='Logo URL', related="logo_id.url")
    logo_id = fields.Many2one('ir.attachment', string='Course logo')
    category = fields.Selection(
        [('organization', 'Organization'), ('course', 'Course'), ('syllabus', 'Syllabus')])
    user_ids = fields.One2many('res.users', 'group_id', string='Users')
    course_ids = fields.One2many('opencourse.course', 'group_id', string='Courses')

    course_count = fields.Integer(compute='_compute_course_count', string='Course count')

    def _compute_course_count(self):
        course_count = 0
        for group in self:
            course_count = len(group.course_ids)
            for child_group in group.child_ids:
                course_count += child_group.course_count
            group.course_count = course_count
