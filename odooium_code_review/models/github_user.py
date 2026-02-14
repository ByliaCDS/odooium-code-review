# -*- coding: utf-8 -*-

from odoo import models, fields, api


class GitHubUser(models.Model):
    _name = 'odooium.github_user'
    _description = 'GitHub User Mapping'
    _order = 'github_login'

    github_id = fields.Integer('GitHub ID', required=True, index=True)
    github_login = fields.Char('GitHub Login', required=True, index=True)
    github_avatar_url = fields.Char('Avatar URL')
    
    # Odoo User Mapping
    odoo_user_id = fields.Many2one('res.users', string='Odoo User', ondelete='cascade')
    
    # Metadata
    last_sync_at = fields.Datetime('Last Sync', default=fields.Datetime.now)
    active = fields.Boolean('Active', default=True)
    
    _sql_constraints = [
        ('github_id_unique', 'UNIQUE(github_id)', 'GitHub ID must be unique'),
        ('github_login_unique', 'UNIQUE(github_login)', 'GitHub login must be unique'),
    ]
    
    def action_sync_github_data(self):
        """Sync user data from GitHub"""
        self.ensure_one()
        github_service = self.env['odooium.github_service']
        user_data = github_service.get_github_user(self.github_login)
        
        if user_data:
            self.write({
                'github_avatar_url': user_data.get('avatar_url'),
                'last_sync_at': fields.Datetime.now(),
            })
        
        return True
    
    @api.model
    def find_or_create(self, github_user_data):
        """Find existing GitHub user or create new mapping"""
        github_id = github_user_data.get('id')
        login = github_user_data.get('login')
        
        user = self.search([('github_id', '=', github_id)], limit=1)
        
        if not user:
            # Find Odoo user by email
            odoo_user = self.env['res.users'].search([
                ('email', '=', github_user_data.get('email'))
            ], limit=1)
            
            user = self.create({
                'github_id': github_id,
                'github_login': login,
                'github_avatar_url': github_user_data.get('avatar_url'),
                'odoo_user_id': odoo_user.id if odoo_user else None,
            })
        else:
            # Update existing
            user.write({
                'github_login': login,
                'github_avatar_url': github_user_data.get('avatar_url'),
                'last_sync_at': fields.Datetime.now(),
            })
        
        return user
