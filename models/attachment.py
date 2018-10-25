from odoo import models, fields, api
import datetime
from odoo.exceptions import UserError, ValidationError
import boto3
import boto
import os


class Attachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    @api.multi
    def unlink(self):
        cr, uid, context = self.env.args
        if "account" in context:
            account = context["account"]
            for attachment in self:
                s3_storage = attachment.url.startswith('https://s3') if attachment.url else False
                if s3_storage:
                    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY', None)
                    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY', None)
                    try:
                        client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                                              aws_secret_access_key=AWS_SECRET_KEY)
                        client.delete_object(Bucket=account.s3_bucket, Key=attachment.datas_fname)
                    except Exception as exc:
                        print 'Remove old file S3 error ', exc
                else:
                    try:
                        os.remove(self.store_fname)
                    except Exception as exc:
                        print 'Remove old file error : %s' % self.store_fname, exc
            return super(Attachment, self).unlink()

    @api.multi
    def write(self, vals):
        cr, uid, context = self.env.args
        if "account" in context:
            account = context["account"]
            for attachment in self:
                file_change = attachment.datas_fname and attachment.datas_fname != vals[
                    "datas_fname"] if 'datas_fname' in vals else False
                s3_storage = attachment.url.startswith('https://s3') if attachment.url else False
                if not file_change:
                    continue
                if s3_storage:
                    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY', None)
                    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY', None)
                    try:
                        client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                                              aws_secret_access_key=AWS_SECRET_KEY)
                        client.delete_object(Bucket=account.s3_bucket, Key=attachment.datas_fname)
                    except Exception as exc:
                        print 'Replace old file S3 error ', exc
                else:
                    try:
                        os.remove(self.store_fname)
                    except Exception as exc:
                        print 'Replace old file error : %s' % self.store_fname, exc

        return super(Attachment, self).write(vals)
