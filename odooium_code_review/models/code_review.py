# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CodeReview(models.Model):
    _name = 'odooium.code_review'
    _description = 'Code Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'created_at desc'

    # Pull Request
    pr_id = fields.Many2one('odooium.pull_request', string='Pull Request', required=True, ondelete='cascade')
    
    # Reviewer
    reviewer = fields.Char('Reviewer', help='AI or human reviewer name')
    reviewer_type = fields.Selection([
        ('ai', 'AI Reviewer'),
        ('human', 'Human Reviewer'),
    ], string='Reviewer Type', default='ai', required=True)
    reviewer_user_id = fields.Many2one('res.users', string='Reviewer User', ondelete='set null')
    
    # AI Model (if AI review)
    ai_model = fields.Char('AI Model Used', help='e.g., gpt-4, claude-3')
    
    # Review Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True)
    
    # Review Results
    score = fields.Integer('Score (0-100)', help='Overall quality score')
    summary = fields.Html('Summary')
    
    # Statistics
    critical_count = fields.Integer('Critical Issues', compute='_compute_comment_stats', store=True)
    high_count = fields.Integer('High Issues', compute='_compute_comment_stats', store=True)
    medium_count = fields.Integer('Medium Issues', compute='_compute_comment_stats', store=True)
    low_count = fields.Integer('Low Issues', compute='_compute_comment_stats', store=True)
    info_count = fields.Integer('Info Count', compute='_compute_comment_stats', store=True)
    total_comments = fields.Integer('Total Comments', compute='_compute_comment_stats', store=True)
    
    # Timing
    started_at = fields.Datetime('Started')
    completed_at = fields.Datetime('Completed')
    duration = fields.Float('Duration (minutes)', compute='_compute_duration', store=True, digits=(3, 1))
    
    # Metadata
    created_at = fields.Datetime('Created', default=fields.Datetime.now)
    github_review_id = fields.Integer('GitHub Review ID')
    
    # Relations
    comment_ids = fields.One2many('odooium.review_comment', 'review_id', string='Comments')
    
    @api.depends('comment_ids.severity')
    def _compute_comment_stats(self):
        for review in self:
            review.critical_count = len(review.comment_ids.filtered(lambda c: c.severity == 'critical'))
            review.high_count = len(review.comment_ids.filtered(lambda c: c.severity == 'high'))
            review.medium_count = len(review.comment_ids.filtered(lambda c: c.severity == 'medium'))
            review.low_count = len(review.comment_ids.filtered(lambda c: c.severity == 'low'))
            review.info_count = len(review.comment_ids.filtered(lambda c: c.severity == 'info'))
            review.total_comments = len(review.comment_ids)
    
    @api.depends('started_at', 'completed_at')
    def _compute_duration(self):
        for review in self:
            if review.started_at and review.completed_at:
                delta = review.completed_at - review.started_at
                review.duration = delta.total_seconds() / 60.0
            else:
                review.duration = 0.0
    
    def action_view_pr(self):
        """View related Pull Request"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'odooium.pull_request',
            'res_id': self.pr_id.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
    
    def action_resubmit_for_review(self):
        """Resubmit for AI review (if issues were fixed)"""
        self.ensure_one()
        self.write({'status': 'pending'})
        self.pr_id.action_start_ai_review()
        return True
