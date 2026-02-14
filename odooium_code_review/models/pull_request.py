# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PullRequest(models.Model):
    _name = 'odooium.pull_request'
    _description = 'GitHub Pull Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'created_at desc'

    # GitHub Fields
    github_id = fields.Integer('GitHub PR ID', required=True, index=True, copy=False)
    number = fields.Integer('PR Number', required=True, index=True)
    title = fields.Char('Title', required=True, tracking=True)
    description = fields.Html('Description')
    author = fields.Char('Author', required=True)
    author_github_id = fields.Integer('Author GitHub ID')
    author_avatar = fields.Char('Author Avatar')
    branch = fields.Char('Branch')
    base_branch = fields.Char('Base Branch')
    commit_sha = fields.Char('Commit SHA')
    
    # Repository
    repository_id = fields.Many2one('odooium.github_repository', string='Repository', required=True, ondelete='cascade')
    
    # PR State
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('merged', 'Merged'),
    ], string='State', default='open', tracking=True)
    
    # Review Status
    review_status = fields.Selection([
        ('pending', 'Pending Review'),
        ('reviewing', 'AI Reviewing'),
        ('completed', 'Review Completed'),
        ('failed', 'Review Failed'),
    ], string='Review Status', default='pending', tracking=True)
    
    # AI Review Fields
    ai_score = fields.Integer('AI Score', help='0-100 score from AI review', copy=False)
    ai_model_used = fields.Char('AI Model Used')
    ai_review_started_at = fields.Datetime('AI Review Started')
    ai_review_completed_at = fields.Datetime('AI Review Completed')
    ai_review_duration = fields.Float('Review Duration (minutes)', compute='_compute_review_duration', store=True, digits=(3, 1))
    
    # Review Summary
    total_comments = fields.Integer('Total Comments', compute='_compute_review_stats', store=True)
    critical_issues = fields.Integer('Critical Issues', compute='_compute_review_stats', store=True)
    high_issues = fields.Integer('High Issues', compute='_compute_review_stats', store=True)
    medium_issues = fields.Integer('Medium Issues', compute='_compute_review_stats', store=True)
    low_issues = fields.Integer('Low Issues', compute='_compute_review_stats', store=True)
    info_count = fields.Integer('Info Count', compute='_compute_review_stats', store=True)
    
    # Odoo Integration
    task_id = fields.Many2one('project.task', string='Odoo Task', ondelete='set null')
    project_id = fields.Many2one('project.project', related='task_id.project_id', store=True, string='Project')
    stage_id = fields.Many2one('project.task.type', related='task_id.stage_id', store=True, string='Task Stage')
    
    # Metadata
    created_at = fields.Datetime('Created at', required=True, default=fields.Datetime.now)
    updated_at = fields.Datetime('Updated at')
    closed_at = fields.Datetime('Closed/Merged at')
    url = fields.Char('GitHub URL', compute='_compute_url', store=True)
    active = fields.Boolean('Active', default=True)
    
    # Relations
    review_ids = fields.One2many('odooium.code_review', 'pr_id', string='Reviews')
    comment_ids = fields.One2many('odooium.review_comment', compute='_compute_comments', store=False)
    
    # Computed Fields
    last_review_id = fields.Many2one('odooium.code_review', compute='_compute_last_review', store=True)
    last_review_summary = fields.Text('Last Review Summary', related='last_review_id.summary', store=False)
    review_count = fields.Integer('Review Count', compute='_compute_review_stats', store=True)
    
    @api.depends('repository_id.full_name', 'number')
    def _compute_url(self):
        for pr in self:
            if pr.repository_id.full_name and pr.number:
                pr.url = f"https://github.com/{pr.repository_id.full_name}/pull/{pr.number}"
            else:
                pr.url = False
    
    @api.depends('review_ids.comment_ids.severity')
    def _compute_review_stats(self):
        for pr in self:
            all_comments = pr.review_ids.mapped('comment_ids')
            pr.total_comments = len(all_comments)
            pr.critical_issues = len(all_comments.filtered(lambda c: c.severity == 'critical'))
            pr.high_issues = len(all_comments.filtered(lambda c: c.severity == 'high'))
            pr.medium_issues = len(all_comments.filtered(lambda c: c.severity == 'medium'))
            pr.low_issues = len(all_comments.filtered(lambda c: c.severity == 'low'))
            pr.info_count = len(all_comments.filtered(lambda c: c.severity == 'info'))
            pr.review_count = len(pr.review_ids)
    
    @api.depends('review_ids')
    def _compute_last_review(self):
        for pr in self:
            pr.last_review_id = pr.review_ids.sorted('created_at', reverse=True)[:1].id
    
    @api.depends('review_ids.comment_ids')
    def _compute_comments(self):
        for pr in self:
            pr.comment_ids = pr.review_ids.mapped('comment_ids').sorted('created_at', reverse=True)
    
    @api.depends('ai_review_started_at', 'ai_review_completed_at')
    def _compute_review_duration(self):
        for pr in self:
            if pr.ai_review_started_at and pr.ai_review_completed_at:
                delta = pr.ai_review_completed_at - pr.ai_review_started_at
                pr.ai_review_duration = delta.total_seconds() / 60.0
            else:
                pr.ai_review_duration = 0.0
    
    def name_get(self):
        result = []
        for pr in self:
            name = f'#{pr.number}: {pr.title}'
            result.append((pr.id, name))
        return result
    
    def action_start_ai_review(self):
        """Start AI review for this PR"""
        self.ensure_one()
        if self.review_status != 'pending':
            raise UserError(_('Only pending PRs can be reviewed'))
        
        self.write({
            'review_status': 'reviewing',
            'ai_review_started_at': fields.Datetime.now()
        })
        
        # Queue AI review job
        self.with_delay(priority=5, description=f'AI Review PR #{self.number}')._run_ai_review()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('AI Review Started'),
                'message': _('The AI review has been queued for PR #%s') % self.number,
                'type': 'info',
            }
        }
    
    def _run_ai_review(self):
        """Run AI review (queued job)"""
        self.ensure_one()
        
        try:
            # Fetch PR code diff from GitHub
            github_service = self.env['odooium.github_service']
            code_diff = github_service.get_pr_diff(self.repository_id, self.number)
            
            if not code_diff:
                self.write({
                    'review_status': 'failed',
                    'ai_review_completed_at': fields.Datetime.now()
                })
                return
            
            # Run AI review
            ai_service = self.env['odooium.ai_review_service']
            review_result = ai_service.review_code(
                code_diff,
                self.repository_id,
                self.ai_model_used or self.repository_id.ai_model
            )
            
            # Create review record
            review_vals = {
                'pr_id': self.id,
                'reviewer': 'AI',
                'reviewer_type': 'ai',
                'status': 'completed',
                'started_at': self.ai_review_started_at,
                'completed_at': fields.Datetime.now(),
                'score': review_result.get('score', 0),
                'summary': review_result.get('summary', ''),
                'ai_model': self.ai_model_used or self.repository_id.ai_model,
            }
            review = self.env['odooium.code_review'].create(review_vals)
            
            # Create review comments
            for comment_data in review_result.get('comments', []):
                self.env['odooium.review_comment'].create({
                    'review_id': review.id,
                    'pr_id': self.id,
                    'file_path': comment_data.get('file_path'),
                    'line_number': comment_data.get('line_number'),
                    'comment': comment_data.get('comment'),
                    'severity': comment_data.get('severity', 'medium'),
                    'rule': comment_data.get('rule', ''),
                    'is_ai': True,
                })
            
            # Post review to GitHub
            github_service.post_review_comment(
                self.repository_id, 
                self.number, 
                review_result.get('summary', ''),
                review_result.get('comments', [])
            )
            
            # Update PR status
            self.write({
                'review_status': 'completed',
                'ai_review_completed_at': fields.Datetime.now(),
                'ai_score': review_result.get('score', 0)
            })
            
            # Update Odoo task
            self._update_task_after_review(review_result)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.write({
                'review_status': 'failed',
                'ai_review_completed_at': fields.Datetime.now()
            })
            self.message_post(
                body=_('AI review failed: %s') % str(e),
                message_type='comment'
            )
    
    def _update_task_after_review(self, review_result):
        """Update Odoo task after AI review"""
        self.ensure_one()
        if not self.task_id:
            return
        
        score = review_result.get('score', 0)
        message = _('AI review completed with score: **%s**\n\n') % score
        message += _('* Critical issues: %s\n') % self.critical_issues
        message += _('* High issues: %s\n') % self.high_issues
        message += _('* Medium issues: %s\n') % self.medium_issues
        message += _('* Low issues: %s\n') % self.low_issues
        message += _('* Info: %s') % self.info_count
        
        self.task_id.message_post(body=message)
        
        # Move to next stage if score is good
        if score >= 80:
            ready_stage = self.env['project.task.type'].search([
                ('project_ids', 'in', self.project_id.id),
                '|', ('name', 'ilike', 'Ready'), ('name', 'ilike', 'Review')
            ], limit=1)
            if ready_stage:
                self.task_id.stage_id = ready_stage.id
    
    def action_view_on_github(self):
        """Open PR on GitHub"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.url,
            'target': 'new',
        }
    
    def action_view_task(self):
        """View linked Odoo task"""
        self.ensure_one()
        if not self.task_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Task'),
                    'message': _('No task is linked to this PR'),
                    'type': 'warning',
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'res_id': self.task_id.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
    
    @api.model
    def get_dashboard_stats(self):
        """Get statistics for dashboard"""
        prs = self.search([('active', '=', True)])
        
        return {
            'total_prs': len(prs),
            'pending_prs': len(prs.filtered(lambda p: p.review_status == 'pending')),
            'reviewing_prs': len(prs.filtered(lambda p: p.review_status == 'reviewing')),
            'completed_prs': len(prs.filtered(lambda p: p.review_status == 'completed')),
            'today_prs': len(prs.filtered(lambda p: p.created_at.date() == fields.Date.today())),
            'avg_score': prs.mapped('ai_score') and sum(prs.mapped('ai_score')) / len(prs.mapped('ai_score')) or 0,
            'avg_review_time': self._get_avg_review_time(),
        }
    
    def _get_avg_review_time(self):
        """Get average review time in minutes"""
        completed_prs = self.search([
            ('active', '=', True),
            ('ai_review_started_at', '!=', False),
            ('ai_review_completed_at', '!=', False),
        ])
        
        if not completed_prs:
            return 0
        
        total_time = sum([
            (pr.ai_review_completed_at - pr.ai_review_started_at).total_seconds()
            for pr in completed_prs
        ])
        
        return round(total_time / len(completed_prs) / 60.0, 2)
