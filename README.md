# Odooium - AI Code Review for Odoo Development Teams

🐰 **Odooium** is an AI-powered code review platform designed specifically for Odoo development teams. Built on Odoo 19 with a modern OWL frontend (POS-style UI).

## 🎯 Features

### Core Feature: AI Code Review (Rabbit Code)

- 🤖 **AI-Powered Reviews** - Automatic code reviews using GPT-4 or Claude
- 🔗 **GitHub Integration** - Webhook-based PR monitoring
- 📊 **Real-time Dashboard** - Modern OWL-based dashboard with live updates
- 🔔 **Smart Notifications** - Automatic notifications on review completion
- 📋 **Odoo Integration** - Seamless task integration with Odoo Project
- ✅ **Odoo-Specific Rules** - Reviews based on Odoo ORM, security, and best practices
- 📈 **Analytics** - Review statistics and performance metrics

### Key Capabilities

- **Automatic Review Triggering** - Reviews start automatically when PRs are opened
- **Severity Scoring** - Issues categorized as Critical, High, Medium, Low, Info
- **Comment Management** - All review comments tracked and searchable
- **GitHub Comment Posting** - Reviews posted directly to PRs
- **Task Sync** - Odoo tasks created and updated based on PR status
- **Review History** - Complete audit trail of all reviews

## 🏗️ Architecture

### Technology Stack

| Component | Technology |
|-----------|-------------|
| **Platform** | Odoo 19 |
| **Database** | Separate Odooium Database |
| **Frontend** | OWL (Odoo Web Library) - Modern, Reactive |
| **Backend** | Python (Odoo ORM) |
| **Queue** | queue_job (Odoo background jobs) |
| **AI Engine** | OpenAI GPT-4 / Anthropic Claude |
| **GitHub** | GitHub Webhooks + OAuth |

### Module Structure

```
odooium_code_review/
├── models/                 # Odoo models
│   ├── pull_request.py   # Pull Request model
│   ├── code_review.py    # Code Review model
│   ├── review_comment.py # Review Comment model
│   ├── github_repository.py
│   ├── github_user.py
│   └── odooium_config.py
├── controllers/             # HTTP controllers
│   ├── auth_controller.py     # GitHub OAuth
│   ├── webhook_controller.py   # GitHub webhooks
│   └── api_controller.py       # API endpoints
├── services/               # Business logic services
│   ├── github_service.py      # GitHub API client
│   └── ai_review_service.py   # AI review engine
├── components/             # OWL frontend components
├── static/src/             # Frontend assets
│   ├── js/                 # OWL JavaScript
│   ├── scss/               # Modern SCSS styles
│   └── xml/                # OWL templates
├── views/                  # Odoo views
└── security/               # Access rights
```

## 📦 Installation

### Prerequisites

- Odoo 19 (with separate database for Odooium)
- GitHub App (for OAuth & Webhooks)
- OpenAI API Key or Anthropic API Key
- Odoo Project module (for task integration)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cds-solutions/odooium.git
   cd odooium/odooium_code_review
   ```

2. **Install module in Odoo:**
   - Go to Apps → Update Apps List
   - Upload the module
   - Click "Install"

3. **Configure GitHub:**
   - Go to Odooium → Configuration
   - Add GitHub OAuth credentials
   - Add Webhook secret

4. **Configure AI Service:**
   - Add OpenAI or Anthropic API key
   - Select default AI model

5. **Add Repositories:**
   - Go to Odooium → Repositories
   - Click "New"
   - Enter GitHub repository details
   - Enable auto-review if desired

## 🎨 Modern UI Features

### POS-Style Design

- **Single-Page Application** - No page reloads, instant navigation
- **Real-time Updates** - Live PR status updates
- **Dark Mode Support** - Developer-friendly dark theme
- **Responsive Design** - Works on desktop, tablet, mobile
- **Keyboard Shortcuts** - Efficient keyboard navigation
- **Component-Based** - Reusable OWL components

### Dashboard Layout

```
┌─────────────────────────────────────────┐
│  🐰 Odooium              [Actions]   │
├─────────────────────────────────────────┤
│  Statistics Cards                      │
│  - Total PRs   - Pending          │
│  - Reviewing   - Completed         │
│                                       │
│  Recent Pull Requests (Table)          │
│  - # | Title | Author | Status     │
│    | Score | Time | Actions       │
└─────────────────────────────────────────┘
```

## 🔐 Security

- **GitHub OAuth** - Secure authentication
- **Webhook Signature Verification** - Validating GitHub events
- **Role-Based Access Control** - User, Manager, Admin roles
- **Access Rights** - Granular permissions per model
- **Secure API Keys** - Encrypted storage

## 📊 Database Schema

### Pull Request Model

| Field | Type | Description |
|-------|------|-------------|
| github_id | Integer | GitHub PR ID |
| number | Integer | PR Number |
| title | Char | PR Title |
| author | Char | Author GitHub login |
| review_status | Selection | pending, reviewing, completed, failed |
| ai_score | Integer | 0-100 score from AI review |
| state | Selection | open, closed, merged |

### Code Review Model

| Field | Type | Description |
|-------|------|-------------|
| pr_id | Many2one | Related Pull Request |
| reviewer | Char | AI or human reviewer name |
| reviewer_type | Selection | ai or human |
| score | Integer | 0-100 quality score |
| summary | Html | Review summary |
| status | Selection | pending, in_progress, completed |

### Review Comment Model

| Field | Type | Description |
|-------|------|-------------|
| review_id | Many2one | Related Code Review |
| file_path | Char | File path in repository |
| line_number | Integer | Line number |
| comment | Html | Comment text |
| severity | Selection | critical, high, medium, low, info |
| rule | Char | Rule violated |
| rule_category | Selection | orm, security, performance, etc. |

## 🚀 Usage

### For Developers

1. **Open a PR in GitHub** - Review starts automatically (if enabled)
2. **View Dashboard** - Check review status in Odooium
3. **Read Comments** - Review comments posted to GitHub PR
4. **Fix Issues** - Address issues and update code
5. **Re-review** - Push updates for re-review

### For Team Leads

1. **Monitor Reviews** - Dashboard shows all active reviews
2. **Review Statistics** - Track team performance
3. **Manage Repositories** - Add/remove monitored repositories
4. **Configure Settings** - AI model, auto-review settings

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

Odooium is licensed under OPL-1 (Odoo Proprietary License v1.0).

## 👥 Support

For issues, questions, or feature requests:
- 📧 Email: support@cds-solutions.com
- 🐛 GitHub Issues: https://github.com/cds-solutions/odooium/issues

## 🎉 Acknowledgments

- Built with **Odoo 19**
- Frontend: **OWL** (Odoo Web Library)
- AI: **OpenAI** / **Anthropic**
- Design inspiration: **Odoo POS**

---

**Made with ❤️ by CDS Solutions**
