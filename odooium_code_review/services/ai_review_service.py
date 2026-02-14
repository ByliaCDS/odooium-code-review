# -*- coding: utf-8 -*-

from odoo import models, api, _
import logging
import json

_logger = logging.getLogger(__name__)


class AIReviewService(models.Model):
    _name = 'odooium.ai_review_service'
    _description = 'AI Code Review Service'

    @api.model
    def get_ai_provider(self):
        """Get AI provider (OpenAI or Anthropic)"""
        default_model = self.env['ir.config_parameter'].sudo().get_param('odooium.default_ai_model', 'gpt-4')
        
        if default_model.startswith('gpt'):
            return 'openai'
        elif default_model.startswith('claude'):
            return 'anthropic'
        return 'openai'

    @api.model
    def get_api_key(self, provider):
        """Get API key for provider"""
        if provider == 'openai':
            return self.env['ir.config_parameter'].sudo().get_param('odooium.openai.api_key')
        elif provider == 'anthropic':
            return self.env['ir.config_parameter'].sudo().get_param('odooium.anthropic.api_key')
        return None

    @api.model
    def test_connection(self):
        """Test connection to AI service"""
        try:
            provider = self.get_ai_provider()
            api_key = self.get_api_key(provider)
            
            if not api_key:
                return {
                    'success': False,
                    'message': 'API key not configured'
                }
            
            # Test with simple request
            if provider == 'openai':
                import openai
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                return {
                    'success': True,
                    'message': f'Connected to {provider}',
                    'model': response.model
                }
            elif provider == 'anthropic':
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-3",
                    max_tokens=5,
                    messages=[{"role": "user", "content": "Hello"}]
                )
                return {
                    'success': True,
                    'message': f'Connected to {provider}',
                    'model': response.model
                }
        except Exception as e:
            _logger.error('AI connection test failed: %s', e)
            return {
                'success': False,
                'message': str(e)
            }

    @api.model
    def review_code(self, code_diff, repository, ai_model=None):
        """Review code diff using AI"""
        try:
            provider = self.get_ai_provider()
            api_key = self.get_api_key(provider)
            
            if not api_key:
                return {
                    'score': 0,
                    'summary': 'AI API key not configured',
                    'comments': []
                }
            
            model = ai_model or self.env['ir.config_parameter'].sudo().get_param('odooium.default_ai_model', 'gpt-4')
            
            # Build prompt
            prompt = self._build_review_prompt(code_diff, repository)
            
            _logger.info('Starting AI code review with model: %s', model)
            
            # Call AI
            if provider == 'openai':
                result = self._review_with_openai(api_key, model, prompt)
            elif provider == 'anthropic':
                result = self._review_with_anthropic(api_key, model, prompt)
            else:
                return {
                    'score': 0,
                    'summary': f'Unknown AI provider: {provider}',
                    'comments': []
                }
            
            # Parse and validate result
            parsed_result = self._parse_review_result(result)
            
            _logger.info('AI review completed. Score: %s, Comments: %s', 
                        parsed_result.get('score'), len(parsed_result.get('comments', [])))
            
            return parsed_result
        
        except Exception as e:
            _logger.exception('Error in AI review')
            return {
                'score': 0,
                'summary': f'Error during review: {str(e)}',
                'comments': []
            }

    @api.model
    def _build_review_prompt(self, code_diff, repository):
        """Build prompt for AI code review"""
        
        # Get Odoo-specific rules
        odoo_rules = self._get_odoo_rules()
        
        # Limit diff size if needed
        max_lines = int(self.env['ir.config_parameter'].sudo().get_param('odooium.max_diff_lines', '5000'))
        if len(code_diff.split('\n')) > max_lines:
            code_diff = '\n'.join(code_diff.split('\n')[:max_lines])
            code_diff += f"\n\n[NOTE: Diff truncated at {max_lines} lines for review]"
        
        prompt = f"""You are an expert code reviewer specializing in Odoo development. Review the following code diff and provide constructive feedback.

Repository: {repository.full_name}

Code Diff:
```diff
{code_diff}
```

Odoo Best Practices & Rules:
{odoo_rules}

Review Guidelines:
1. Check for Odoo ORM patterns (@api.model, @api.depends, @api.constrains)
2. Look for security vulnerabilities (SQL injection, XSS)
3. Identify performance issues (N+1 queries, inefficient loops)
4. Check for code style violations
5. Ensure proper error handling
6. Verify correct field definitions and model structure
7. Check for proper use of decorators
8. Look for missing documentation
9. Identify potential bugs or logic errors

Please respond in the following JSON format:
{{
    "score": <overall score from 0-100>,
    "summary": "<brief summary of the review, highlighting main issues>",
    "comments": [
        {{
            "file_path": "<relative file path>",
            "line_number": <line number or approximate>,
            "comment": "<specific feedback or issue description>",
            "severity": "<critical|high|medium|low|info>",
            "rule": "<which rule was violated or best practice>",
            "rule_category": "<orm|security|performance|style|documentation|best_practice|error|other>"
        }}
    ]
}}

Scoring Guidelines:
- 90-100: Excellent code, follows all best practices
- 80-89: Good code with minor issues
- 70-79: Decent code with some issues
- 60-69: Code needs improvements
- Below 60: Significant issues present
- Subtract 10 points for each critical issue
- Subtract 5 points for each high severity issue
- Subtract 2 points for each medium severity issue

Focus on actionable, specific feedback. Be constructive and helpful.
"""
        return prompt

    @api.model
    def _get_odoo_rules(self):
        """Get Odoo-specific coding rules"""
        return """
1. ORM Patterns:
   - Models must inherit from 'models.Model'
   - Use @api.model for class methods
   - Use @api.depends for computed fields
   - Use @api.constrains for constraints
   - Use @api.onchange for onchange methods
   - Use self.env['model.name'] to access models
   - Never use raw SQL without good reason
   - Use ORM methods (search, read, write, create, unlink)

2. Model Structure:
   - Define _name, _description, _inherit, _order
   - Use proper field types (Char, Text, Many2one, One2many, Many2many, etc.)
   - Set required=True for mandatory fields
   - Use store=True for computed fields if used in searches
   - Use copy=True for fields that should be copied
   - Use index=True for frequently searched fields

3. Security:
   - Never interpolate user input in SQL queries
   - Use parameterized queries or ORM methods
   - Validate and sanitize user input
   - Use proper access rights (ir.model.access.csv, record rules)
   - Never expose sensitive data in API responses

4. Performance:
   - Avoid N+1 queries (use prefetch_related)
   - Use search_read() instead of search() + read()
   - Use batch operations when possible
   - Cache frequently accessed data
   - Use compute fields with @api.depends instead of cron
   - Lazy load related records when possible

5. Code Style:
   - Follow PEP 8 style guide
   - Use meaningful variable and method names
   - Add docstrings to methods
   - Keep methods focused and concise
   - Avoid deep nesting (max 3-4 levels)
   - Use constants instead of magic numbers

6. Error Handling:
   - Use UserError for user-facing errors
   - Use ValidationError for constraint violations
   - Try-except for external API calls
   - Log errors with appropriate level
   - Provide helpful error messages

7. Views:
   - Use QWeb/OWL templates
   - Use proper view inheritance
   - Set unique priorities
   - Use groups for access control
   - Use proper widget types

8. Controllers:
   - Use @http.route decorator
   - Set appropriate auth (public, user)
   - Use CSRF protection for POST requests
   - Return JSON or appropriate response type
   - Handle errors gracefully
"""

    @api.model
    def _review_with_openai(self, api_key, model, prompt):
        """Review code using OpenAI"""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code reviewer specializing in Odoo development. Provide constructive, actionable feedback."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            _logger.error('OpenAI API error: %s', e)
            raise

    @api.model
    def _review_with_anthropic(self, api_key, model, prompt):
        """Review code using Anthropic Claude"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            
            response = client.messages.create(
                model=model,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        
        except Exception as e:
            _logger.error('Anthropic API error: %s', e)
            raise

    @api.model
    def _parse_review_result(self, result_text):
        """Parse AI review response"""
        try:
            # Try to extract JSON from response
            start = result_text.find('{')
            end = result_text.rfind('}') + 1
            json_str = result_text[start:end]
            
            result = json.loads(json_str)
            
            # Validate structure
            if 'score' not in result:
                result['score'] = 0
            if 'summary' not in result:
                result['summary'] = 'No summary provided'
            if 'comments' not in result:
                result['comments'] = []
            
            # Validate comments
            for comment in result['comments']:
                if 'severity' not in comment:
                    comment['severity'] = 'medium'
                if 'file_path' not in comment:
                    comment['file_path'] = 'Unknown'
                if 'line_number' not in comment:
                    comment['line_number'] = 0
                if 'rule_category' not in comment:
                    comment['rule_category'] = 'best_practice'
            
            return result
        
        except Exception as e:
            _logger.error('Failed to parse AI review: %s', e)
            return {
                'score': 0,
                'summary': f'Failed to parse AI review: {str(e)}',
                'comments': []
            }
