# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from odoo.exceptions import UserError, ValidationError
import boto3
import boto
import os


class Course(models.Model):
    _name = 'opencourse.course'
    _description = 'Course'

    supervisor_id = fields.Many2one('res.users', string='Supervisor')
    supervisor_name = fields.Char(related='supervisor_id.name', string='Supervisor name', readonly=True)
    name = fields.Char(string='Name', required=True)
    intro_video_url = fields.Char(string='Intro Video URL', related="intro_video_id.url")
    intro_video_id = fields.Many2one('ir.attachment', string='Intro video')
    description = fields.Text(string='Description')
    mission = fields.Text(string='Mission')
    audience = fields.Text(string='Audince')
    level = fields.Selection(
        [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], default="beginner")
    code = fields.Char(string='Code')
    summary = fields.Text(string='Video Intro URL')
    status = fields.Selection(
        [('open', 'Open'), ('closed', 'Closed'), ('initial', 'Initial')], default="open")
    logo_url = fields.Char(string='Logo URL', related="logo_id.url")
    logo_id = fields.Many2one('ir.attachment', string='Course logo')
    group_id = fields.Many2one('res.groups', string='Group')
    group_name = fields.Char(related='group_id.name', string='Group name', readonly=True)
    faq_ids = fields.One2many('opencourse.course_faq', 'course_id', string='FAQ list')
    material_ids = fields.One2many('opencourse.course_material', 'course_id', string='Material list')
    unit_ids = fields.One2many('opencourse.course_unit', 'course_id', string='Unit list')
    prequisite_course_id = fields.Many2one('opencourse.course', string='Course name')
    prequisite_course_name = fields.Char(related='prequisite_course_id.name', string='Preqiosite course name',
                                         readonly=True)
    syllabus_id = fields.Many2one('opencourse.syllabus', string='Syllabus')
    syllabus_status = fields.Selection(related='syllabus_id.status', string='Syllabus status', readonly=True)
    complete_unit_by_order = fields.Boolean(related='syllabus_id.complete_unit_by_order',
                                            string='Complete unit by order')
    unit_count = fields.Integer(related='syllabus_id.unit_count', string='Course unit count', readonly=True)
    member_ids = fields.One2many('opencourse.course_member', 'course_id', string='Course members')
    rating_ids = fields.One2many('opencourse.course_rating', 'course_id', string='Course ratings')
    teacher = fields.Char(compute='_compute_teacher', string='Teacher')
    teacher_image = fields.Binary(compute='_compute_teacher_image', string='Teacher image')
    length = fields.Integer(compute='_compute_length', string='Length')
    view_count = fields.Integer(string='View count')
    rating = fields.Integer(compute='_compute_rating', string='Rating')
    learning_path_id = fields.Many2one("opencourse.learning_path", string="Learning path")
    metadata = fields.Char(string="Metadata")

    def _compute_teacher(self):
        for course in self:
            for teacher in self.env['opencourse.course_member'].search(
                    [('course_id', '=', course.id), ('role', '=', 'teacher')]):
                course.teacher = teacher.name

    def _compute_teacher_image(self):
        for course in self:
            for teacher in self.env['opencourse.course_member'].search(
                    [('course_id', '=', course.id), ('role', '=', 'teacher')]):
                course.teacher_image = teacher.image

    def _compute_length(self):
        for course in self:
            length = 0
            for video in self.env['opencourse.video_lecture'].search([('course_id', '=', course.id)]):
                length += video.length
            course.length = length

    def _compute_rating(self):
        for course in self:
            sum = 0
            ratings = self.env['opencourse.course_rating'].search([('course_id', '=', course.id)])
            for rating in ratings:
                sum += rating.grade
            if not len(ratings):
                course.rating = sum
            else:
                course.rating = sum / len(ratings)

    @api.model
    def create(self, vals):
        course = super(Course, self).create(vals)
        syllabus = self.env['opencourse.syllabus'].create({'course_id': course.id, 'name': course.name})
        self.env['opencourse.course_member'].create(
            {'course_id': course.id, 'user_id': course.supervisor_id.id, 'role': 'supervisor'})
        course.write({'syllabus_id': syllabus.id})
        return course

    @api.model
    def enroll(self, params):
        successList = []
        failList = []
        courseId = params["courseId"]
        userIds = params["userIds"]
        for course in self.env['opencourse.course'].browse(courseId):
            if course.prequisite_course_id:
                for user in self.env['res.users'].browse(userIds):
                    fail = True
                    for member in user.course_member_ids:
                        if member.course_id.id == course.prequisite_course_id.id and member.enroll_status == 'completed':
                            fail = False
                            break
                    if fail:
                        failList.append(user.id)
                    else:
                        successList.append(user.id)
            else:
                successList = userIds
            for user in self.env['res.users'].browse(successList):
                course.registerCourseMember(user, 'student')
            return {'success': successList, 'fail': failList}

    @api.model
    def enroll_staff(self, params):
        courseId = params["courseId"]
        userIds = params["userIds"]
        for course in self.env['opencourse.course'].browse(courseId):
            for user in self.env['res.users'].browse(userIds):
                course.registerCourseMember(user, 'teacher')
            return {'success': userIds, 'fail': []}

    @api.model
    def open(self, params):
        courseId = params["courseId"]
        for course in self.env["opencourse.course"].browse(courseId):
            for student in self.env['opencourse.course_member'].search(
                    [('course_id', '=', courseId), ('role', '=', 'student')]):
                if student.enroll_status != 'completed':
                    self.env.ref(self._module + "." + "course_open_template").send_mail(student.id, force_send=False)
            course.write({'status': 'open'})
            return True

    @api.model
    def close(self, params):
        courseId = params["courseId"]
        for course in self.env["opencourse.course"].browse(courseId):
            for student in self.env['opencourse.course_member'].search(
                    [('course_id', '=', courseId), ('role', '=', 'student')]):
                if student.enroll_status != 'completed':
                    self.env.ref(self._module + "." + "course_close_template").send_mail(student.id, force_send=False)
            course.write({'status': 'closed'})
            return True

    def registerCourseMember(self, user, role):
        member = self.env['opencourse.course_member'].create({'role': role,
                                                              'course_id': self.id, 'user_id': user.id,
                                                              'status': 'active',
                                                              'enroll_status': 'registered',
                                                              'date_register': datetime.datetime.now()})
        self.env.ref(self._module + "." + "course_register_template").send_mail(member.id, force_send=False)
        return member

    @api.multi
    def unlink(self):
        for member in self.env['opencourse.course_member'].search([('course_id', '=', self.id)]):
            member.unlink()
        if self.intro_video_id:
            self.intro_video_id.unlink()
        if self.syllabus_id:
            self.syllabus_id.unlink()
        for material in self.material_ids:
            material.unlink()
        for unit in self.unit_ids:
            unit.unlink()
        for faq in self.faq_ids:
            faq.unlink()
        for rating in self.rating_ids:
            rating.unlink()
        return super(Course, self).unlink()

    @api.multi
    def write(self, vals):
        if self.intro_video_id and "intro_video_id" in vals and self.intro_video_id.id != vals["intro_video_id"]:
            self.intro_video_id.unlink()
        return super(Course, self).write(vals)


class CourseSyllabus(models.Model):
    _name = 'opencourse.syllabus'
    _description = 'Syllabus'

    complete_unit_by_order = fields.Boolean(name="Complete unit by order", default=False)
    course_id = fields.Many2one('opencourse.course', string='Course')
    supervisor_id = fields.Many2one('res.users', related="course_id.supervisor_id", string='Administrator')
    supervisor_name = fields.Char(related='course_id.supervisor_name', string='Supervisor name', readonly=True)
    unit_ids = fields.One2many('opencourse.course_unit', 'syllabus_id', string='Course units')
    member_ids = fields.One2many('opencourse.course_member', 'syllabus_id', string='Course members')
    name = fields.Char(string='Name')
    status = fields.Selection(
        [('draft', 'draft'), ('published', 'Published'), ('unpublished', 'unpublished')], default="draft")
    unit_count = fields.Integer(compute='_compute_unit_count', string='Unit count')

    def _compute_unit_count(self):
        for syllabus in self:
            units = self.env['opencourse.course_unit'].search(
                [('syllabus_id', '=', syllabus.id), ('type', '!=', 'folder')])
            syllabus.unit_count = len(units)


class CourseUnit(models.Model):
    _name = 'opencourse.course_unit'
    _description = 'Course unit'

    supervisor_id = fields.Many2one('res.users', related="syllabus_id.supervisor_id", string='Administrator')
    parent_id = fields.Many2one('opencourse.course_unit', string='Parent')
    order = fields.Integer(string='Order', default=0)
    syllabus_id = fields.Many2one('opencourse.syllabus', string='Syllabus')
    course_id = fields.Many2one('opencourse.course', related='syllabus_id.course_id', string='Course', readonly=True)
    name = fields.Char(string='Name', required=True)
    icon = fields.Char(name="Icon")
    status = fields.Selection(
        [('draft', 'draft'), ('published', 'Published'), ('unpublished', 'unpublished')], default="published")
    type = fields.Selection(
        [('folder', 'Folder'), ('html', 'HTML'), ('slide', 'Slide'), ('scorm', 'SCORM'), ('exercise', 'Exercise'),
         ('video', 'Video')])
    slide_lecture_id = fields.Many2one('opencourse.slide_lecture', string='Slide lecture')
    html_lecture_id = fields.Many2one('opencourse.html_lecture', string='HTML lecture')
    video_lecture_id = fields.Many2one('opencourse.video_lecture', string='Video lecture')
    scorm_lecture_id = fields.Many2one('opencourse.scorm_lecture', string='SCORM lecture')
    length = fields.Integer(related='video_lecture_id.length', string='Video length', readonly=True)

    @api.model
    def create(self, vals):
        unit = super(CourseUnit, self).create(vals)
        if unit.type == 'html':
            html_lecture = self.env['opencourse.html_lecture'].create({'unit_id': unit.id})
            unit.write({'html_lecture_id': html_lecture.id})
        if unit.type == 'slide':
            slide_lecture = self.env['opencourse.slide_lecture'].create({'unit_id': unit.id})
            unit.write({'slide_lecture_id': slide_lecture.id})
        if unit.type == 'video':
            video_lecture = self.env['opencourse.video_lecture'].create({'unit_id': unit.id})
            unit.write({'video_lecture_id': video_lecture.id})
        if unit.type == 'scorm':
            scorm_lecture = self.env['opencourse.scorm_lecture'].create({'unit_id': unit.id})
            unit.write({'scorm_lecture_id': scorm_lecture.id})
        return unit

    @api.multi
    def unlink(self):
        if self.slide_lecture_id:
            self.slide_lecture_id.unlink()
        if self.html_lecture_id:
            self.html_lecture_id.unlink()
        if self.video_lecture_id:
            self.video_lecture_id.unlink()
        if self.scorm_lecture_id:
            self.scorm_lecture_id.unlink()
        return super(CourseUnit, self).unlink()


class SlideLecture(models.Model):
    _name = 'opencourse.slide_lecture'
    _description = 'Slide lecture'

    slide_url = fields.Char(string='Slide URL', related='slide_file_id.url')
    slide_file_id = fields.Many2one('ir.attachment', string='Slide')
    filename = fields.Char(string='File name', related='slide_file_id.datas_fname', stored=True)
    unit_id = fields.Many2one('opencourse.course_unit', string='Course unit')
    course_id = fields.Many2one('opencourse.course', related='unit_id.course_id', string='Course', readonly=True)

    @api.multi
    def write(self, vals):
        if self.slide_file_id and "slide_file_id" in vals and self.slide_file_id.id != vals["slide_file_id"]:
            self.slide_file_id.unlink()
        return super(SlideLecture, self).write(vals)

    @api.multi
    def unlink(self):
        if self.slide_file_id:
            self.slide_file_id.unlink()
        return super(SlideLecture, self).unlink()


class HtmlLecture(models.Model):
    _name = 'opencourse.html_lecture'
    _description = 'slide bai giang kieu html'

    content = fields.Text(string='Content')
    unit_id = fields.Many2one('opencourse.course_unit', string='Course unit')
    course_id = fields.Many2one('opencourse.course', related='unit_id.course_id', string='Course', readonly=True)


class VideoLecture(models.Model):
    _name = 'opencourse.video_lecture'
    _description = 'Slide bai giang kieu video'

    transcript = fields.Text(string='Transcript')
    video_url = fields.Char(string='Video URL', related='attachment_id.url', stored=True)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')
    unit_id = fields.Many2one('opencourse.course_unit', string='Course unit')
    length = fields.Integer(string='Length in minutes')
    course_id = fields.Many2one('opencourse.course', related='unit_id.course_id', string='Course', readonly=True)

    @api.multi
    def write(self, vals):
        if self.attachment_id and "attachment_id" in vals and self.attachment_id.id != vals["attachment_id"]:
            self.attachment_id.unlink()
        return super(VideoLecture, self).write(vals)

    @api.multi
    def unlink(self):
        if self.attachment_id:
            self.attachment_id.unlink()
        return super(VideoLecture, self).unlink()


class SCORMLecture(models.Model):
    _name = 'opencourse.scorm_lecture'
    _description = 'Slide kieu scorm'

    base_url = fields.Char(string='Base URL')
    entry_file = fields.Text(string='Entry file')
    package_url = fields.Char(string='Package URL', related='package_file_id.url')
    package_file_id = fields.Many2one('ir.attachment', string='Package file')
    unit_id = fields.Many2one('opencourse.course_unit', string='Course unit')
    course_id = fields.Many2one('opencourse.course', related='unit_id.course_id', string='Course', readonly=True)

    @api.multi
    def write(self, vals):
        if self.package_file_id and "package_file_id" in vals and self.package_file_id.id != vals["package_file_id"]:
            self.package_file_id.unlink()
        return super(SCORMLecture, self).write(vals)

    @api.multi
    def unlink(self):
        if self.package_file_id:
            self.package_file_id.unlink()
        return super(SCORMLecture, self).unlink()


class CourseMember(models.Model):
    _name = 'opencourse.course_member'
    _description = 'Course member'

    syllabus_id = fields.Many2one('opencourse.syllabus', string='Syllabus', readonly=True)
    course_id = fields.Many2one('opencourse.course', string='Course')
    user_id = fields.Many2one('res.users', string='User')
    email = fields.Char(related='user_id.email', string='Email', readonly=True)
    phone = fields.Char(related='user_id.phone', string='Phone', readonly=True)
    intro = fields.Text(related='user_id.intro', string='Intro', readonly=True)
    group_id = fields.Many2one('res.groups', related='user_id.group_id', string='Training group', readonly=True)
    group_name = fields.Char(related='group_id.name', string='Group name', readonly=True)
    name = fields.Char(related='user_id.name', string='User name', readonly=True)
    image = fields.Binary(related='user_id.image', string='Image', readonly=True)
    login = fields.Char(related='user_id.login', string='User login', readonly=True)
    course_teacher = fields.Char(related='course_id.teacher', string='Course teacher', readonly=True)
    course_name = fields.Char(related='course_id.name', string='Course name', readonly=True)
    course_logo = fields.Char(related='course_id.logo_url', string='Course logo', readonly=True)
    course_code = fields.Char(related='course_id.code', string='Course code', readonly=True)
    course_group_name = fields.Char(related='course_id.group_name', string='Course group name', readonly=True)
    course_group_id = fields.Many2one('res.groups', related='course_id.group_id', string='Course group ID',
                                      readonly=True)
    status = fields.Selection(
        [('active', 'Active'), ('withdraw', 'Withdraw'), ('suspend', 'Suspend')], default="active")
    role = fields.Selection(
        [('student', 'Student'), ('teacher', 'Teacher'), ('editor', 'Editor'), ('supervisor', 'Supervisor')])
    enroll_status = fields.Selection(
        [('in-study', 'In-study'), ('completed', 'Completed'), ('registered', 'Registered')], default="registered")
    date_register = fields.Datetime('Register date')
    unit_complete = fields.Integer(compute='_compute_unit_complete', string='Unit complete')
    percent_complete = fields.Float(compute='_compute_percent_complete', string='Percent complete')

    def _compute_unit_complete(self):
        for member in self:
            unit_ids = [log.res_id for log in self.env['opencourse.course_log'].search(
                [('code', '=', 'COMPLETE_COURSE_UNIT'), ('member_id', '=', member.id)])]
            member.unit_complete = len(set(unit_ids))

    def _compute_percent_complete(self):
        for member in self:
            unit_ids = [log.res_id for log in self.env['opencourse.course_log'].search(
                [('code', '=', 'COMPLETE_COURSE_UNIT'), ('member_id', '=', member.id)])]
            if member.course_id.unit_count == 0:
                member.percent_complete = 0
            else:
                member.percent_complete = len(set(unit_ids)) * 100 / member.course_id.unit_count

    @api.model
    def complete_course(self, params):
        memberId = params["memberId"]
        for member in self.env['opencourse.course_member'].browse(memberId):
            member.write({'enroll_status': 'completed'})
        return True

    @api.multi
    def unlink(self):
        return super(CourseMember, self).unlink()

    @api.model
    def create(self, vals):
        members = []
        if 'user_id' in vals and vals['user_id']:
            members = self.env['opencourse.course_member'].search(
                [('user_id', '=', vals['user_id']), ('role', '=', vals['role']), ('course_id', '=', vals['course_id'])])
        if len(members) > 0:
            m = members[0]
        else:
            m = super(CourseMember, self).create(vals)
        return m


class CourseRating(models.Model):
    _name = 'opencourse.course_rating'

    course_id = fields.Many2one('opencourse.course', string='Course')
    user_id = fields.Many2one('res.users', string='Rate user')
    user_name = fields.Char(related='user_id.name', string='User name', readonly=True)
    user_logo = fields.Binary(related='user_id.image', string='User logo', readonly=True)
    comment = fields.Text(string='Comment')
    grade = fields.Integer(string='Rating start')


class CourseMaterial(models.Model):
    _name = 'opencourse.course_material'

    course_id = fields.Many2one('opencourse.course', string='Course')
    name = fields.Char(string='Name')
    type = fields.Selection(
        [('video', 'Video'), ('audio', 'Audio'), ('file', 'File')])
    url = fields.Char(string='Attachment URL', related='material_file_id.url')
    material_file_id = fields.Many2one('ir.attachment', string='Material file')
    filename = fields.Char(string='Attachment Filename', related='material_file_id.datas_fname')

    @api.multi
    def write(self, vals):
        if self.material_file_id and "material_file_id" in vals and self.material_file_id.id != vals[
            "material_file_id"]:
            self.material_file_id.unlink()
        return super(CourseMaterial, self).write(vals)

    @api.multi
    def unlink(self):
        if self.material_file_id:
            self.material_file_id.unlink()
        return super(CourseMaterial, self).unlink()


class FAQ(models.Model):
    _name = 'opencourse.course_faq'

    question = fields.Text(string='Question')
    answer = fields.Text(string='Answer')
    course_id = fields.Many2one('opencourse.course', string='Course')


class LearningPath(models.Model):
    _name = 'opencourse.learning_path'

    name = fields.Char(string='Name')
    summary = fields.Text(string='summary')
    intro_video_url = fields.Char(string='Intro video URL', related="intro_video_id.url")
    intro_video_id = fields.Many2one('ir.attachment', string='Intro video file')
    item_ids = fields.One2many('opencourse.learning_path_item', 'path_id', string='Path items')
    group_name = fields.Text(compute='_compute_group_name', string='Group name', store=True)
    group_ids = fields.Many2many('res.groups', compute='_compute_group_ids', string='Group ids', store=True)
    logo_url = fields.Char(string='Logo URL', related="logo_id.url")
    logo_id = fields.Many2one('ir.attachment', string='Course logo')
    course_count = fields.Integer(compute='_compute_course_count', string='Course count')
    length = fields.Integer(compute='_compute_path_length', string='Path length')
    member_count = fields.Integer(compute='_compute_member_count', string='Member count')
    course_ids = fields.One2many("opencourse.course", "learning_path_id", string="Course")

    @api.multi
    def write(self, vals):
        if self.intro_video_id and "intro_video_id" in vals and self.intro_video_id.id != vals["intro_video_id"]:
            self.intro_video_id.unlink()
        return super(LearningPath, self).write(vals)

    @api.multi
    def unlink(self):
        if self.intro_video_id:
            self.intro_video_id.unlink()
        return super(LearningPath, self).unlink()

    def _compute_course_count(self):
        for path in self:
            path.course_count = len(path.item_ids)

    def _compute_member_count(self):
        for path in self:
            count = 0
            for item in path.item_ids:
                count += len(item.member_ids)
            path.member_count = count

    def _compute_path_length(self):
        for path in self:
            length = 0
            for item in path.item_ids:
                length += item.course_length
            path.length = length

    def _compute_group_name(self):
        for path in self:
            path.group_name = ','.join([item.group_name for item in path.item_ids])

    def _compute_group_ids(self):
        for path in self:
            group_ids = [item.group_id.id for item in path.item_ids]
            path.group_ids = self.env['res.groups'].browse(set(group_ids))


class LearningPathItem(models.Model):
    _name = 'opencourse.learning_path_item'

    course_id = fields.Many2one('opencourse.course', string='Courses')
    course_status = fields.Selection(related='course_id.status', string='Course status', readonly=True)
    group_id = fields.Many2one('res.groups', related='course_id.group_id', string='Group name', readonly=True)
    group_name = fields.Char(related='group_id.name', string='Group name', readonly=True)
    course_name = fields.Char(related='course_id.name', string='Course name', readonly=True)
    course_teacher = fields.Char(related='course_id.teacher', string='Course teacher', readonly=True)
    course_summary = fields.Text(related='course_id.summary', string='Course summary', readonly=True)
    course_logo = fields.Char(related='course_id.logo_url', string='Course logo', readonly=True)
    supervisor_name = fields.Char(related='course_id.supervisor_name', string='Supervisor name', readonly=True)
    path_id = fields.Many2one('opencourse.learning_path', string='Learning path')
    order = fields.Integer(string='Order')
    member_ids = fields.One2many('opencourse.course_member', related='course_id.member_ids', string='Course member',
                                 readonly=True)
    course_length = fields.Integer(related='course_id.length', string='Course length', readonly=True)
