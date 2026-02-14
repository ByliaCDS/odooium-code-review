# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class OdooiumAuthController(http.Controller):
    
    @http.route('/odooium/auth/github', type='http', auth='public', methods=['GET'], website=True)
    def github_auth(self, **kwargs):
        """Redirect to GitHub OAuth"""
        
        client_id = request.env['ir.config_parameter'].sudo().get_param('odooium.github.oauth.client_id')
        redirect_uri = request.env['ir.config_parameter'].sudo().get_param('odooium.github.redirect_uri')
        scope = 'user:email,repo:status,read:org'
        
        if not client_id:
            return request.redirect('/web?error=github_not_configured')
        
        github_auth_url = f'https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope={scope}'
        
        return request.redirect(github_auth_url)
    
    @http.route('/odooium/auth/github/callback', type='http', auth='public', methods=['GET'], website=True)
    def github_callback(self, **kwargs):
        """Handle GitHub OAuth callback"""
        
        code = kwargs.get('code')
        error = kwargs.get('error')
        
        if error:
            _logger.error('GitHub OAuth error: %s', error)
            return request.redirect(f'/web?error=github_auth_{error}')
        
        if not code:
            return request.redirect('/web?error=no_code')
        
        try:
            # Exchange code for access token
            token_result = self._exchange_code_for_token(code)
            
            if not token_result.get('access_token'):
                return request.redirect('/web?error=token_exchange_failed')
            
            # Fetch user profile
            user_data = self._fetch_github_user(token_result.get('access_token'))
            
            if not user_data:
                return request.redirect('/web?error=fetch_user_failed')
            
            # Find or create Odoo user
            odoo_user = self._find_or_create_user(user_data, token_result)
            
            # Log in user
            request.session.authenticate(
                request.env.cr.dbname,
                odoo_user.login,
                request.env.user.password
            )
            
            return request.redirect('/odooium/dashboard')
        
        except Exception as e:
            _logger.exception('GitHub callback error')
            return request.redirect(f'/web?error={str(e)}')
    
    def _exchange_code_for_token(self, code):
        """Exchange OAuth code for access token"""
        import requests
        
        client_id = request.env['ir.config_parameter'].sudo().get_param('odooium.github.oauth.client_id')
        client_secret = request.env['ir.config_parameter'].sudo().get_param('odooium.github.oauth.client_secret')
        
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
        }
        
        response = requests.post(
            'https://github.com/login/oauth/access_token',
            data=data,
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code != 200:
            _logger.error('Token exchange failed: %s', response.text)
            return {}
        
        return response.json()
    
    def _fetch_github_user(self, access_token):
        """Fetch GitHub user profile"""
        import requests
        
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(
            'https://api.github.com/user',
            headers=headers
        )
        
        if response.status_code != 200:
            _logger.error('Failed to fetch GitHub user: %s', response.text)
            return None
        
        return response.json()
    
    def _find_or_create_user(self, github_user_data, token_result):
        """Find or create Odoo user"""
        github_id = github_user_data.get('id')
        login = github_user_data.get('login')
        email = github_user_data.get('email')
        name = github_user_data.get('name') or login
        avatar_url = github_user_data.get('avatar_url')
        access_token = token_result.get('access_token')
        
        # Find GitHub user mapping
        github_user = request.env['odooium.github_user'].sudo().search([
            ('github_id', '=', github_id)
        ], limit=1)
        
        if not github_user:
            # Try to find Odoo user by email
            odoo_user = None
            if email:
                odoo_user = request.env['res.users'].sudo().search([
                    ('email', '=', email)
                ], limit=1)
            
            # If no Odoo user found, use current user or create new one
            if not odoo_user:
                odoo_user = request.env.user
            
            # Create GitHub user mapping
            github_user = request.env['odooium.github_user'].sudo().create({
                'github_id': github_id,
                'github_login': login,
                'github_avatar_url': avatar_url,
                'odoo_user_id': odoo_user.id,
            })
        else:
            odoo_user = github_user.odoo_user_id
            # Update GitHub user data
            github_user.write({
                'github_login': login,
                'github_avatar_url': avatar_url,
            })
        
        # Update Odoo user with GitHub info
        if odoo_user and not odoo_user.github_id:
            odoo_user.write({
                'github_id': github_id,
                'github_login': login,
                'github_avatar_url': avatar_url,
                'github_token': access_token,
            })
        
        return odoo_user
