# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GitHubRepository(models.Model):
    _name = 'odooium.github_repository'
    _description = 'GitHub Repository'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Repository Name', required=True, index=True)
    full_name = fields.Char('Full Name', required=True, index=True)  # e.g., CDS/odoo-project
    owner = fields.Char('Owner', required=True)
    github_id = fields.Integer('GitHub ID', required=True, index=True)
    webhook_id = fields.Char('Webhook ID')
    
    # GitHub Integration
    is_active = fields.Boolean('Active', default=True, tracking=True)
    last_sync_at = fields.Datetime('Last Sync')
    access_token = fields.Char('Access Token')
    
    # Code Review Settings
    auto_review_enabled = fields.Boolean('Auto AI Review', default=True, help='Automatically start AI review on PR open')
    ai_model = fields.Selection([
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('claude-3', 'Claude 3'),
        ('claude-3.5', 'Claude 3.5'),
    ], string='AI Model', default='gpt-4', required=True)
    
    # Odoo Integration
    project_id = fields.Many2one('project.project', string='Project')
    create_tasks = fields.Boolean('Create Odoo Tasks', default=True, help='Create task for each PR')
    
    # Statistics
    pr_count = fields.Integer('Total PRs', default=0)
    review_count = fields.Integer('Total Reviews', default=0)
    avg_score = fields.Float('Average Score', compute='_compute_statistics', store=True, digits=(3, 1))
    
    # Computed Fields
    pull_request_ids = fields.One2many('odooium.pull_request', 'repository_id', string='Pull Requests')
    active_pr_count = fields.Integer('Active PRs', compute='_compute_statistics', store=True)
    
    @api.depends('pull_request_ids.status', 'pull_request_ids.ai_score')
    def _compute_statistics(self):
        for repo in self:
            active_prs = repo.pull_request_ids.filtered(lambda pr: pr.status in ['pending', 'reviewing'])
            repo.active_pr_count = len(active_prs)
            repo.pr_count = len(repo.pull_request_ids)
            repo.review_count = len(repo.pull_request_ids.mapped('review_ids'))
            
            completed_reviews = repo.pull_request_ids.mapped('review_ids').filtered(lambda r: r.score > 0)
            if completed_reviews:
                repo.avg_score = sum(completed_reviews.mapped('score')) / len(completed_reviews)
            else:
                repo.avg_score = 0
    
    def action_sync_pull_requests(self):
        """Sync PRs from GitHub"""
        self.ensure_one()
        github_service = self.env['odooium.github_service']
        github_service.sync_repository_prs(self)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Syncing PRs'),
                'message': _('PRs are being synced from GitHub'),
                'type': 'info',
            }
        }
    
    def action_test_webhook(self):
        """Test GitHub webhook"""
        self.ensure_one()
        github_service = self.env['odooium.github_service']
        result = github_service.test_webhook(self)
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Webhook Working'),
                    'message': _('Webhook is configured correctly'),
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Webhook Error'),
                    'message': result.get('message', 'Webhook test failed'),
                    'type': 'danger',
                }
            }
