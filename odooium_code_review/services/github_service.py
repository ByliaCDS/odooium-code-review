# -*- coding: utf-8 -*-

from odoo import models, api, _
import requests
import logging
import json
import hmac
import hashlib

_logger = logging.getLogger(__name__)


class GitHubService(models.Model):
    _name = 'odooium.github_service'
    _description = 'GitHub Service'

    @api.model
    def _get_github_api_base(self):
        """Get GitHub API base URL"""
        return 'https://api.github.com'

    @api.model
    def _get_headers(self, token=None):
        """Get headers for GitHub API requests"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
        }
        if token:
            headers['Authorization'] = f'token {token}'
        return headers

    @api.model
    def _api_request(self, method, endpoint, data=None, token=None):
        """Make API request to GitHub"""
        base_url = self._get_github_api_base()
        url = f'{base_url}{endpoint}'
        headers = self._get_headers(token)
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f'Unsupported method: {method}')
            
            response.raise_for_status()
            return response.json() if response.text else {}
        
        except requests.exceptions.RequestException as e:
            _logger.error('GitHub API request failed: %s', e)
            raise

    @api.model
    def test_connection(self):
        """Test GitHub connection"""
        try:
            # Test with public API
            result = self._api_request('GET', '/user')
            return {
                'success': True,
                'message': 'Successfully connected to GitHub',
                'user': result.get('login')
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    @api.model
    def get_github_user(self, username):
        """Get GitHub user by username"""
        try:
            result = self._api_request('GET', f'/users/{username}')
            return result
        except Exception as e:
            _logger.error('Failed to get GitHub user %s: %s', username, e)
            return None

    @api.model
    def get_repository(self, owner, repo_name, token=None):
        """Get repository details"""
        try:
            result = self._api_request('GET', f'/repos/{owner}/{repo_name}', token=token)
            return result
        except Exception as e:
            _logger.error('Failed to get repository %s/%s: %s', owner, repo_name, e)
            return None

    @api.model
    def get_pull_requests(self, repository, state='open', token=None):
        """Get pull requests for a repository"""
        try:
            owner, repo = repository.full_name.split('/')
            result = self._api_request('GET', f'/repos/{owner}/{repo}/pulls?state={state}', token=token)
            return result
        except Exception as e:
            _logger.error('Failed to get PRs for %s: %s', repository.full_name, e)
            return []

    @api.model
    def get_pull_request(self, repository, pr_number, token=None):
        """Get single pull request"""
        try:
            owner, repo = repository.full_name.split('/')
            result = self._api_request('GET', f'/repos/{owner}/{repo}/pulls/{pr_number}', token=token)
            return result
        except Exception as e:
            _logger.error('Failed to get PR #%s for %s: %s', pr_number, repository.full_name, e)
            return None

    @api.model
    def get_pr_diff(self, repository, pr_number, token=None):
        """Get PR diff (patch)"""
        try:
            owner, repo = repository.full_name.split('/')
            headers = self._get_headers(token)
            headers['Accept'] = 'application/vnd.github.v3.patch'
            
            url = f'{self._get_github_api_base()}/repos/{owner}/{repo}/pulls/{pr_number}'
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            return response.text
        
        except Exception as e:
            _logger.error('Failed to get PR diff for #%s: %s', pr_number, e)
            return None

    @api.model
    def get_pr_files(self, repository, pr_number, token=None):
        """Get files changed in PR"""
        try:
            owner, repo = repository.full_name.split('/')
            result = self._api_request('GET', f'/repos/{owner}/{repo}/pulls/{pr_number}/files', token=token)
            return result
        except Exception as e:
            _logger.error('Failed to get PR files for #%s: %s', pr_number, e)
            return []

    @api.model
    def create_webhook(self, repository):
        """Create webhook for repository"""
        try:
            owner, repo = repository.full_name.split('/')
            
            redirect_uri = self.env['ir.config_parameter'].sudo().get_param('odooium.github.redirect_uri')
            webhook_url = f'{redirect_uri.replace("/auth/github/callback", "/webhook/github")}'
            
            data = {
                'name': 'web',
                'active': True,
                'events': ['pull_request', 'pull_request_review', 'push'],
                'config': {
                    'url': webhook_url,
                    'content_type': 'json',
                    'secret': repository.access_token or self.env['ir.config_parameter'].sudo().get_param('odooium.github.webhook_secret'),
                    'insecure_ssl': '0'
                }
            }
            
            result = self._api_request('POST', f'/repos/{owner}/{repo}/hooks', data=data, token=repository.access_token)
            
            return {
                'success': True,
                'webhook_id': result.get('id'),
                'message': 'Webhook created successfully'
            }
        except Exception as e:
            _logger.error('Failed to create webhook for %s: %s', repository.full_name, e)
            return {
                'success': False,
                'message': str(e)
            }

    @api.model
    def post_review_comment(self, repository, pr_number, summary, comments, token=None):
        """Post review comment to GitHub PR"""
        try:
            owner, repo = repository.full_name.split('/')
            headers = self._get_headers(token)
            
            # Post PR comment (not inline review for now)
            comment_body = f"## 🐰 Odooium AI Review\n\n{summary}\n\n"
            
            if comments:
                comment_body += "\n### Issues Found:\n\n"
                for comment in comments:
                    severity_icon = comment.get('severity', 'info')
                    comment_body += f"- **{severity_icon.upper()}**: `{comment.get('file_path')}`:{comment.get('line_number')} - {comment.get('comment')}\n"
            
            url = f'{self._get_github_api_base()}/repos/{owner}/{repo}/issues/{pr_number}/comments'
            response = requests.post(url, headers=headers, json={'body': comment_body}, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'comment_id': response.json().get('id'),
                'message': 'Review comment posted successfully'
            }
        except Exception as e:
            _logger.error('Failed to post review comment: %s', e)
            return {
                'success': False,
                'message': str(e)
            }

    @api.model
    def sync_repository_prs(self, repository):
        """Sync all PRs from GitHub to Odoo"""
        try:
            github_prs = self.get_pull_requests(repository, state='all', token=repository.access_token)
            
            synced_count = 0
            for pr_data in github_prs:
                pr_github_id = pr_data.get('id')
                pr_number = pr_data.get('number')
                
                # Find existing PR
                existing_pr = self.env['odooium.pull_request'].search([
                    ('github_id', '=', pr_github_id),
                    ('repository_id', '=', repository.id)
                ], limit=1)
                
                # Determine state
                state = 'open'
                if pr_data.get('closed_at'):
                    state = 'closed'
                elif pr_data.get('merged_at'):
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
                    'state': state,
                    'repository_id': repository.id,
                    'created_at': pr_data.get('created_at'),
                    'updated_at': pr_data.get('updated_at'),
                }
                
                if state in ['closed', 'merged']:
                    vals['closed_at'] = pr_data.get('closed_at') or pr_data.get('merged_at')
                
                if existing_pr:
                    existing_pr.write(vals)
                else:
                    new_pr = self.env['odooium.pull_request'].create(vals)
                    
                    # Create Odoo task if enabled
                    if repository.create_tasks:
                        self._create_task_for_pr(new_pr, repository)
                    
                    # Start AI review if enabled
                    if repository.auto_review_enabled and state == 'open':
                        new_pr.action_start_ai_review()
                    
                    synced_count += 1
            
            repository.write({'last_sync_at': fields.Datetime.now()})
            
            return {
                'success': True,
                'synced': synced_count,
                'message': f'Synced {synced_count} PRs'
            }
        
        except Exception as e:
            _logger.error('Failed to sync PRs: %s', e)
            return {
                'success': False,
                'message': str(e)
            }

    @api.model
    def _create_task_for_pr(self, pr, repository):
        """Create Odoo task for PR"""
        try:
            if not repository.project_id:
                return
            
            # Get default stage
            default_stage = self.env['project.task.type'].search([
                ('project_ids', 'in', repository.project_id.id),
                ('sequence', '=', 1)
            ], limit=1)
            
            # Find or create Odoo user for GitHub author
            github_user = self.env['odooium.github_user'].search([
                ('github_id', '=', pr.author_github_id)
            ], limit=1)
            
            assignee_id = github_user.odoo_user_id.id if github_user and github_user.odoo_user_id else None
            
            # Create task
            task_vals = {
                'name': f'[PR #{pr.number}] {pr.title}',
                'project_id': repository.project_id.id,
                'stage_id': default_stage.id if default_stage else None,
                'description': pr.description,
                'user_id': assignee_id,
            }
            
            task = self.env['project.task'].create(task_vals)
            pr.write({'task_id': task.id, 'project_id': repository.project_id.id})
            
            _logger.info('Created Odoo task %s for PR %s', task.id, pr.number)
        
        except Exception as e:
            _logger.error('Failed to create task for PR %s: %s', pr.number, e)

    @api.model
    def test_webhook(self, repository):
        """Test webhook configuration"""
        try:
            # List webhooks to verify
            owner, repo = repository.full_name.split('/')
            webhooks = self._api_request('GET', f'/repos/{owner}/{repo}/hooks', token=repository.access_token)
            
            redirect_uri = self.env['ir.config_parameter'].sudo().get_param('odooium.github.redirect_uri')
            webhook_url = f'{redirect_uri.replace("/auth/github/callback", "/webhook/github")}'
            
            # Find our webhook
            for hook in webhooks:
                if hook.get('config', {}).get('url') == webhook_url:
                    return {
                        'success': True,
                        'message': 'Webhook is configured and active',
                        'webhook': hook
                    }
            
            return {
                'success': False,
                'message': 'Webhook not found'
            }
        except Exception as e:
            _logger.error('Failed to test webhook: %s', e)
            return {
                'success': False,
                'message': str(e)
            }
