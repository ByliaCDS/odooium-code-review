# -*- coding: utf-8 -*-
{
    'name': 'Odooium - AI Code Review',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'AI-Powered Code Review for Odoo Development Teams',
    'description': """
        Odooium AI Code Review (Rabbit Code)
        ========================================
        
        An intelligent code review platform for Odoo development teams.
        
        Key Features:
        * GitHub PR Integration via Webhooks
        * AI-Powered Code Reviews (GPT-4/Claude)
        * Real-time Review Dashboard (OWL Modern UI)
        * Automatic Review Comments on PRs
        * Odoo Project/Task Integration
        * Review Analytics & Statistics
        * Odoo-Specific Coding Rules
        * Severity Scoring (Critical, High, Medium, Low)
    """,
    'author': 'CDS Solutions',
    'website': 'https://cds-solutions.com',
    'license': 'OPL-1',
    'depends': [
        'base',
        'mail',
        'web',
        'project',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/odooium_menu_views.xml',
        'views/github_repository_views.xml',
        'views/pull_request_views.xml',
        'views/review_views.xml',
        'views/review_comment_views.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odooium_code_review/static/src/scss/odooium.scss',
            'odooium_code_review/static/src/js/odooium.js',
        ],
        'web.assets_frontend': [
            'odooium_code_review/static/src/scss/odooium.scss',
        ],
    },
    'qweb': [
        'static/src/xml/dashboard_templates.xml',
        'static/src/xml/pull_request_templates.xml',
        'static/src/xml/review_templates.xml',
    ],
    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
