# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    github_id = fields.Integer('GitHub ID')
    github_login = fields.Char('GitHub Login')
    github_token = fields.Char('GitHub Token')
    github_avatar_url = fields.Char('GitHub Avatar URL')
    
    # Code Review Settings
    enable_ai_reviews = fields.Boolean('Enable AI Reviews', default=True)
    auto_start_reviews = fields.Boolean('Auto-Start Reviews on PR Open', default=True)
    review_notification = fields.Boolean('Review Notifications', default=True)
