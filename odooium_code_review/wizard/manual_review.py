# -*- coding: utf-8 -*-

from odoo import models, api, _


class ManualReview(models.TransientModel):
    _name = 'odooium.manual_review'
    _description = 'Manual Review'

    pr_id = fields.Many2one('odooium.pull_request', string='Pull Request', required=True)
    reviewer_comments = fields.Html('Reviewer Comments', required=True)
    score = fields.Integer('Score (0-100)', required=True)
    
    def action_submit_review(self):
        """Submit manual review"""
        self.ensure_one()
        
        # Create review record
        review_vals = {
            'pr_id': self.pr_id.id,
            'reviewer': self.env.user.name,
            'reviewer_type': 'human',
            'reviewer_user_id': self.env.user.id,
            'status': 'completed',
            'started_at': self.pr_id.ai_review_started_at or self.pr_id.created_at,
            'completed_at': fields.Datetime.now(),
            'score': self.score,
            'summary': self.reviewer_comments,
        }
        
        self.env['odooium.code_review'].create(review_vals)
        
        # Post to GitHub
        github_service = self.env['odooium.github_service']
        github_service.post_review_comment(
            self.pr_id.repository_id,
            self.pr_id.number,
            self.reviewer_comments,
            [],
            self.env.user.github_token or self.pr_id.repository_id.access_token
        )
        
        # Update PR status
        self.pr_id.write({'review_status': 'completed'})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'odooium.pull_request',
            'res_id': self.pr_id.id,
            'views': [[False, 'form']],
            'target': 'current',
        }
