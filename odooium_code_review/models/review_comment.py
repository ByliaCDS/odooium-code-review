# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReviewComment(models.Model):
    _name = 'odooium.review_comment'
    _description = 'Review Comment'
    _order = 'created_at desc'

    # Relations
    review_id = fields.Many2one('odooium.code_review', string='Review', required=True, ondelete='cascade')
    pr_id = fields.Many2one('odooium.pull_request', related='review_id.pr_id', store=True, string='Pull Request')
    
    # Comment Details
    file_path = fields.Char('File Path', help='Relative file path in the repository')
    line_number = fields.Integer('Line Number')
    comment = fields.Html('Comment', required=True)
    
    # Severity
    severity = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
        ('info', 'Info'),
    ], string='Severity', default='medium', required=True, tracking=True)
    
    # Rule
    rule = fields.Char('Rule Violated', help='Which rule or best practice was violated')
    rule_category = fields.Selection([
        ('orm', 'ORM Pattern'),
        ('security', 'Security'),
        ('performance', 'Performance'),
        ('style', 'Code Style'),
        ('documentation', 'Documentation'),
        ('best_practice', 'Best Practice'),
        ('error', 'Error/Bug'),
        ('other', 'Other'),
    ], string='Rule Category', default='best_practice')
    
    # Metadata
    is_ai = fields.Boolean('AI Generated', default=True)
    is_resolved = fields.Boolean('Resolved', default=False)
    resolved_at = fields.Datetime('Resolved At')
    resolved_by = fields.Many2one('res.users', string='Resolved By', ondelete='set null')
    
    # GitHub
    github_comment_id = fields.Integer('GitHub Comment ID')
    
    # Timestamps
    created_at = fields.Datetime('Created', default=fields.Datetime.now)
    updated_at = fields.Datetime('Updated', auto_now=True)
    
    @api.model
    def get_severity_colors(self):
        """Get severity colors for dashboard"""
        return {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary',
            'info': 'light',
        }
    
    @api.model
    def get_severity_icons(self):
        """Get severity icons"""
        return {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'info': '🔵',
        }
    
    def action_resolve(self):
        """Mark comment as resolved"""
        self.ensure_one()
        self.write({
            'is_resolved': True,
            'resolved_at': fields.Datetime.now(),
            'resolved_by': self.env.user.id
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Comment Resolved'),
                'message': _('Comment has been marked as resolved'),
                'type': 'success',
            }
        }
    
    def action_reopen(self):
        """Mark comment as unresolved"""
        self.ensure_one()
        self.write({
            'is_resolved': False,
            'resolved_at': False,
            'resolved_by': False
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Comment Reopened'),
                'message': _('Comment has been reopened'),
                'type': 'info',
            }
        }
    
    def action_view_in_pr(self):
        """View comment in GitHub PR"""
        self.ensure_one()
        if not self.pr_id.url or not self.file_path:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cannot View'),
                    'message': _('Cannot view this comment on GitHub'),
                    'type': 'warning',
                }
            }
        
        # Build GitHub URL with file and line
        url = f"{self.pr_id.url}#discussion_r{self.github_comment_id}"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }
