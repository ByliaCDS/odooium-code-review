# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class OdooiumAPIController(http.Controller):
    
    @http.route('/odooium/api/stats', type='json', auth='user')
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            stats = request.env['odooium.pull_request'].get_dashboard_stats()
            return {'success': True, 'data': stats}
        except Exception as e:
            _logger.error('Error getting stats: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/odooium/api/pull_requests', type='json', auth='user', methods=['GET'])
    def get_pull_requests(self, status=None, limit=50, **kwargs):
        """Get pull requests list"""
        try:
            domain = [('active', '=', True)]
            
            if status:
                domain.append(('review_status', '=', status))
            
            prs = request.env['odooium.pull_request'].search_read(
                domain,
                ['id', 'number', 'title', 'author', 'author_avatar', 
                 'review_status', 'ai_score', 'created_at', 'state'],
                limit=min(limit, 100),
                order='created_at desc'
            )
            
            return {'success': True, 'data': prs}
        except Exception as e:
            _logger.error('Error getting PRs: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/odooium/api/pull_request/<int:pr_id>', type='json', auth='user', methods=['GET'])
    def get_pull_request(self, pr_id, **kwargs):
        """Get single pull request with details"""
        try:
            pr = request.env['odooium.pull_request'].browse(pr_id)
            
            if not pr.exists():
                return {'success': False, 'error': 'PR not found'}
            
            data = {
                'id': pr.id,
                'number': pr.number,
                'title': pr.title,
                'description': pr.description,
                'author': pr.author,
                'author_avatar': pr.author_avatar,
                'branch': pr.branch,
                'base_branch': pr.base_branch,
                'state': pr.state,
                'review_status': pr.review_status,
                'ai_score': pr.ai_score,
                'ai_review_started_at': pr.ai_review_started_at,
                'ai_review_completed_at': pr.ai_review_completed_at,
                'ai_review_duration': pr.ai_review_duration,
                'total_comments': pr.total_comments,
                'critical_issues': pr.critical_issues,
                'high_issues': pr.high_issues,
                'medium_issues': pr.medium_issues,
                'low_issues': pr.low_issues,
                'info_count': pr.info_count,
                'created_at': pr.created_at,
                'updated_at': pr.updated_at,
                'url': pr.url,
                'task_id': pr.task_id.id if pr.task_id else None,
                'project_id': pr.project_id.id if pr.project_id else None,
                'reviews': [{
                    'id': r.id,
                    'reviewer': r.reviewer,
                    'reviewer_type': r.reviewer_type,
                    'score': r.score,
                    'summary': r.summary,
                    'status': r.status,
                    'created_at': r.created_at,
                    'total_comments': r.total_comments,
                    'critical_count': r.critical_count,
                    'high_count': r.high_count,
                    'medium_count': r.medium_count,
                    'low_count': r.low_count,
                } for r in pr.review_ids],
                'comments': [{
                    'id': c.id,
                    'file_path': c.file_path,
                    'line_number': c.line_number,
                    'comment': c.comment,
                    'severity': c.severity,
                    'rule': c.rule,
                    'rule_category': c.rule_category,
                    'is_ai': c.is_ai,
                    'is_resolved': c.is_resolved,
                    'created_at': c.created_at,
                } for c in pr.comment_ids[:50]]  # Limit to 50 comments
            }
            
            return {'success': True, 'data': data}
        except Exception as e:
            _logger.error('Error getting PR details: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/odooium/api/reviews', type='json', auth='user', methods=['GET'])
    def get_reviews(self, pr_id=None, limit=20, **kwargs):
        """Get reviews"""
        try:
            domain = []
            
            if pr_id:
                domain.append(('pr_id', '=', pr_id))
            
            reviews = request.env['odooium.code_review'].search_read(
                domain,
                ['id', 'pr_id', 'reviewer', 'reviewer_type', 'score', 
                 'summary', 'status', 'created_at'],
                limit=min(limit, 100),
                order='created_at desc'
            )
            
            return {'success': True, 'data': reviews}
        except Exception as e:
            _logger.error('Error getting reviews: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/odooium/action/start_review', type='json', auth='user', methods=['POST'])
    def action_start_review(self, pr_id, **kwargs):
        """Start AI review for a PR"""
        try:
            pr = request.env['odooium.pull_request'].browse(pr_id)
            
            if not pr.exists():
                return {'success': False, 'error': 'PR not found'}
            
            pr.action_start_ai_review()
            
            return {'success': True, 'message': 'AI review started'}
        except Exception as e:
            _logger.error('Error starting review: %s', e)
            return {'success': False, 'error': str(e)}
    
    @http.route('/odooium/repositories', type='http', auth='user', website=True)
    def repositories_page(self, **kwargs):
        """Repositories management page"""
        return request.render('odooium_code_review.repositories_template', {})
