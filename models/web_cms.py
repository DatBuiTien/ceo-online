# -*- coding: utf-8 -*-

from odoo import models, fields, api


class WebPage(models.Model):
    _name = 'opencourse.web_page'

    order = fields.Integer('Order')
    name = fields.Text('Name')
    code = fields.Char('Code')
    content = fields.Text('Content')
    section_ids = fields.One2many('opencourse.page_section', 'page_id', string="Sections")
    title = fields.Char('Title')
    metadata = fields.Char('metadata')


class PageSection(models.Model):
    _name = 'opencourse.page_section'

    res_model = fields.Char('Resource Model', help="The database object this attachment will be attached to.")
    name = fields.Text('Name')
    code = fields.Char('Code')
    order = fields.Integer('Order')
    content = fields.Text('Content')
    page_id = fields.Many2one('opencourse.web_page', string="Web page")
    page_code = fields.Char('Page code', related="page_id.code", readonly=True)
    item_ids = fields.One2many('opencourse.section_item', 'section_id', string="Items")


class SectionItem(models.Model):
    _name = 'opencourse.section_item'

    res_id = fields.Integer('Resource ID', help="The record id this is attached to.")
    order = fields.Integer('Order')
    section_id = fields.Many2one('opencourse.page_section', string="Section")
    page_id = fields.Many2one('opencourse.web_page', related="section_id.page_id", string="Section item", readonly=True)
    page_code = fields.Char('Page code', related="section_id.page_code", readonly=True)
    section_code = fields.Char('Section code', related="section_id.code", readonly=True)
    name = fields.Char('Name')
    is_hidden = fields.Boolean('Is hidden', default=False)
    title = fields.Char('Title')
    image_url = fields.Char('URL', related="image_file_id.url")
    video_url = fields.Char('URL', related="video_file_id.url")
    web_url = fields.Text('URL')
    content = fields.Text('Content')
    image_file_id = fields.Many2one('ir.attachment', string='Image file')
    video_file_id = fields.Many2one('ir.attachment', string='Video file')

    @api.multi
    def write(self, vals):
        if self.image_file_id and "image_file_id" in vals and self.image_file_id.id != vals["image_file_id"]:
            self.image_file_id.unlink()
        if self.video_file_id and "video_file_id" in vals and self.video_file_id.id != vals["video_file_id"]:
            self.video_file_id.unlink()
        return super(SectionItem, self).write(vals)

    @api.multi
    def unlink(self):
        if self.video_file_id:
            self.video_file_id.unlink()
        if self.image_file_id:
            self.image_file_id.unlink()
        return super(SectionItem, self).unlink()
