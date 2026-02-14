# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, JsonRequest
import logging
import hmac
import hashlib

_logger = logging.getLogger(__name__)


class OdooiumWebhookController(http.Controller):
    
    @http.route('/odooium/webhook/github', type='json', auth='public', methods=['POST'], csrf=False)
    def github_webhook(self, **kwargs):
        """Handle GitHub webhook events"""
        
        # Verify webhook signature
        signature = request.httprequest.headers.get('X-Hub-Signature-256')
        if not self._verify_webhook_signature(signature, request.httprequest.data):
            _logger.warning('Invalid webhook signature')
            return {'status': 'error', 'message': 'Invalid signature'}
        
        # Get event type
        event_type = request.httprequest.headers.get('X-GitHub-Event')
        payload = request.jsonrequest
        
        _logger.info('GitHub webhook received: %s', event_type)
        
        try:
            if event_type == 'pull_request':
                self._handle_pull_request(payload)
            elif event_type == 'pull_request_review':
                self._handle_pull_request_review(payload)
            elif event_type == 'push':
                self._handle_push(payload)
            
            return {'status': 'success'}
        
        except Exception as e:
            _logger.exception('Error processing webhook')
            return {'status': 'error', 'message': str(e)}
    
    def _verify_webhook_signature(self, signature, data):
        """Verify GitHub webhook signature"""
        if not signature:
            return False
        
        webhook_secret = request.env['ir.config_parameter'].sudo().get_param('odooium.github.webhook_secret')
        if not webhook_secret:
            _logger.warning('GitHub webhook secret not configured')
            return False
        
        hash_signature = 'sha256=' + hmac.new(
            webhook_secret.encode(),
            data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(hash_signature, signature)
    
    def _handle_pull_request(self, payload):
        """Handle pull_request event"""
        action = payload.get('action')
        pr_data = payload.get('pull_request')
        repo_data = payload.get('repository')
        
        if not pr_data:
            return
        
        # Find repository
        repo_full_name = repo_data.get('full_name')
        repo = request.env['odooium.github_repository'].sudo().search([
            ('full_name', '=', repo_full_name),
            ('is_active', '=', True)
        ], limit=1)
        
        if not repo:
            _logger.warning('Repository not found: %s', repo_full_name)
            return
        
        # Create or update PR
        pr_github_id = pr_data.get('id')
        pr_number = pr_data.get('number')
        
        existing_pr = request.env['odooium.pull_request'].sudo().search([
            ('github_id', '=', pr_github_id),
            ('repository_id', '=', repo.id)
        ], limit=1)
        
        # Determine state
        state = 'open'
        if action in ['closed', 'closed']:
            state = 'closed'
        elif pr_data.get('merged', False):
            state = 'merged'
        
        vals = {
            'github_id': pr_github_id,
            'number': pr_number,
            'title': pr_data.get('title'),
            'description': pr_data.get('body'),
            'author': pr_data.get('user', {}).get('login'),
            'author_github_id': pr_data.get('user', {}).get('id'),
            'author_avatar': pr_data.get('user', {}).get('avatar_url'),
            'branch': pr_data.get('head', {}).get('ref'),
            'base_branch': pr_data.get('base', {}).get('ref'),
            'commit_sha': pr_data.get('head', {}).get('sha'),
            'repository_id': repo.id,
            'state': state,
            'created_at': pr_data.get('created_at'),
            'updated_at': pr_data.get('updated_at'),
        }
        
        if state in ['closed', 'merged']:
            vals['closed_at'] = pr_data.get('closed_at') or pr_data.get('merged_at')
        
        if existing_pr:
            existing_pr.write(vals)
            pr = existing_pr
        else:
            pr = request.env['odooium.pull_request'].sudo().create(vals)
            
            # Create Odoo task
            if repo.create_tasks:
                github_service = request.env['odooium.github_service']
                github_service._create_task_for_pr(pr, repo)
            
            # Start AI review automatically if enabled
            if repo.auto_review_enabled and action == 'opened':
                pr.with_delay(priority=5).action_start_ai_review()
        
        _logger.info('PR %s: %s', action, pr_number)
    
    def _handle_pull_request_review(self, payload):
        """Handle pull_request_review event (human review)"""
        review_data = payload.get('review')
        pr_data = payload.get('pull_request')
        
        if not pr_data:
            return
        
        # Find PR
        pr_github_id = pr_data.get('id')
        pr = request.env['odooium.pull_request'].sudo().search([
            ('github_id', '=', pr_github_id)
        ], limit=1)
        
        if not pr:
            return
        
        # Find reviewer user
        reviewer_login = review_data.get('user', {}).get('login')
        github_user = request.env['odooium.github_user'].sudo().search([
            ('github_login', '=', reviewer_login)
        ], limit=1)
        
        # Create review record
        review_vals = {
            'pr_id': pr.id,
            'reviewer': review_data.get('user', {}).get('login'),
            'reviewer_type': 'human',
            'reviewer_user_id': github_user.odoo_user_id.id if github_user else None,
            'status': 'completed',
            'started_at': pr.ai_review_started_at or pr.created_at,
            'completed_at': review_data.get('submitted_at'),
            'summary': review_data.get('body', ''),
            'github_review_id': review_data.get('id'),
        }
        
        request.env['odooium.code_review'].sudo().create(review_vals)
        
        _logger.info('Human review created for PR %s by %s', pr.number, reviewer_login)
    
    def _handle_push(self, payload):
        """Handle push event"""
        # Push event can be used to trigger reviews on branch pushes
        ref = payload.get('ref')
        repo_data = payload.get('repository')
        
        _logger.info('Push event on %s: %s', repo_data.get('full_name'), ref)
        
        # Could implement: auto-review pushes to specific branches
        # For now, just log
