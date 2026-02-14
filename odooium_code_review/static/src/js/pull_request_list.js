// Pull Request List Component
/** @odoo-module */
import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PullRequestList extends Component {
    static template = "odooium_code_review.PullRequestList";
    static props = {
        status: { type: String, optional: true },
        limit: { type: Number, optional: true, default: 50 },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            pull_requests: [],
            loading: true,
        });
        
        this.loadPullRequests();
    }

    async loadPullRequests() {
        try {
            this.state.loading = true;
            
            const domain = [['active', '=', True]];
            if (this.props.status) {
                domain.push(['review_status', '=', this.props.status]);
            }
            
            const prs = await this.orm.searchRead(
                'odooium.pull_request',
                domain,
                ['id', 'number', 'title', 'author', 'author_avatar', 
                 'review_status', 'ai_score', 'created_at', 'state'],
                { limit: this.props.limit, order: 'created_at desc' }
            );
            
            this.state.pull_requests = prs.map(pr => ({
                ...pr,
                status_class: this.getStatusClass(pr.review_status),
                score_class: this.getScoreClass(pr.ai_score),
                icon: this.getPRIcon(pr.state),
                time_ago: this.formatTimeAgo(pr.created_at),
            }));
            
            this.state.loading = false;
        } catch (error) {
            console.error('Error loading PRs:', error);
            this.notification.add('Error loading pull requests', { type: 'danger' });
            this.state.loading = false;
        }
    }

    getStatusClass(status) {
        const classes = {
            'pending': 'badge-warning',
            'reviewing': 'badge-info',
            'completed': 'badge-success',
            'failed': 'badge-danger',
        };
        return classes[status] || 'badge-secondary';
    }

    getScoreClass(score) {
        if (score >= 90) return 'bg-success';
        if (score >= 80) return 'bg-success';
        if (score >= 70) return 'bg-warning';
        if (score >= 60) return 'bg-warning';
        return 'bg-danger';
    }

    getPRIcon(state) {
        const icons = {
            'open': 'fa-code-pull-request',
            'closed': 'fa-times-circle',
            'merged': 'fa-code-merge',
        };
        return icons[state] || 'fa-code-pull-request';
    }

    formatTimeAgo(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (days > 0) return `${days}d ago`;
        if (hours > 0) return `${hours}h ago`;
        if (minutes > 0) return `${minutes}m ago`;
        return 'Just now';
    }

    onViewPr(pr) {
        this.action.doActionButton({
            type: 'ir.actions.act_window',
            res_model: 'odooium.pull_request',
            res_id: pr.id,
            views: [[false, 'form']],
            target: 'new',
        });
    }

    onRefresh() {
        this.loadPullRequests();
    }
}

registry.category("actions").add("odooium.pull_request_list", PullRequestList);
