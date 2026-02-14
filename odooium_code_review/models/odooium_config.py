# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OdooiumConfig(models.Model):
    _name = 'odooium.config'
    _description = 'Odooium Configuration'
    _inherit = ['mail.thread']

    # GitHub Configuration
    github_oauth_client_id = fields.Char('GitHub OAuth Client ID', config_parameter='odooium.github.oauth.client_id')
    github_oauth_client_secret = fields.Char('GitHub OAuth Client Secret', config_parameter='odooium.github.oauth.client_secret')
    github_webhook_secret = fields.Char('GitHub Webhook Secret', config_parameter='odooium.github.webhook_secret')
    github_redirect_uri = fields.Char('GitHub OAuth Redirect URI', config_parameter='odooium.github.redirect_uri', default='http://localhost:8069/auth/github/callback')
    
    # AI Configuration
    openai_api_key = fields.Char('OpenAI API Key', config_parameter='odooium.openai.api_key')
    anthropic_api_key = fields.Char('Anthropic API Key', config_parameter='odooium.anthropic.api_key')
    default_ai_model = fields.Selection([
        ('gpt-4', 'GPT-4'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('claude-3', 'Claude 3'),
        ('claude-3.5', 'Claude 3.5'),
    ], string='Default AI Model', default='gpt-4', config_parameter='odooium.default_ai_model')
    
    # Review Settings
    auto_review_enabled = fields.Boolean('Auto-Start Reviews', default=True, config_parameter='odooium.auto_review.enabled', help='Automatically start AI review when PR is opened')
    review_timeout_minutes = fields.Integer('Review Timeout (minutes)', default=30, config_parameter='odooium.review_timeout')
    max_diff_lines = fields.Integer('Max Diff Lines', default=5000, config_parameter='odooium.max_diff_lines', help='Maximum number of diff lines to review')
    
    # Notification Settings
    enable_notifications = fields.Boolean('Enable Notifications', default=True, config_parameter='odooium.notifications.enabled')
    notification_channels = fields.Selection([
        ('email', 'Email Only'),
        ('in_app', 'In-App Only'),
        ('both', 'Email & In-App'),
    ], string='Notification Channels', default='both', config_parameter='odooium.notification_channels')
    
    # Dashboard Settings
    dashboard_refresh_interval = fields.Integer('Dashboard Refresh Interval (seconds)', default=30, config_parameter='odooium.dashboard_refresh_interval')
    dashboard_pr_limit = fields.Integer('Dashboard PR Limit', default=50, config_parameter='odooium.dashboard_pr_limit')
    
    # Odoo Integration
    default_project_id = fields.Many2one('project.project', string='Default Project', config_parameter='odooium.default_project_id')
    create_tasks_automatically = fields.Boolean('Create Tasks Automatically', default=True, config_parameter='odooium.create_tasks_automatically')
    
    # Status
    is_configured = fields.Boolean('Is Configured', compute='_compute_is_configured', store=False)
    
    @api.depends('github_oauth_client_id', 'openai_api_key')
    def _compute_is_configured(self):
        for config in self:
            config.is_configured = bool(
                config.github_oauth_client_id and 
                config.openai_api_key
            )
    
    def action_test_github_connection(self):
        """Test GitHub connection"""
        try:
            github_service = self.env['odooium.github_service']
            result = github_service.test_connection()
            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('GitHub Connection Successful'),
                        'message': result.get('message', 'Connected to GitHub'),
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('GitHub Connection Failed'),
                        'message': result.get('message', 'Cannot connect to GitHub'),
                        'type': 'danger',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': str(e),
                    'type': 'danger',
                }
            }
    
    def action_test_ai_connection(self):
        """Test AI service connection"""
        try:
            ai_service = self.env['odooium.ai_review_service']
            result = ai_service.test_connection()
            if result.get('success'):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('AI Connection Successful'),
                        'message': result.get('message', 'Connected to AI service'),
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('AI Connection Failed'),
                        'message': result.get('message', 'Cannot connect to AI service'),
                        'type': 'danger',
                    }
                }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': str(e),
                    'type': 'danger',
                }
            }
