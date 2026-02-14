// Dashboard Component - Modern POS-style UI
/** @odoo-module */
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useBus } from "@web/core/utils/hooks";

export class OdooiumDashboard extends Component {
    static template = "odooium_code_review.Dashboard";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.bus = useService("bus_service");
        
        this.state = useState({
            stats: {
                total_prs: 0,
                pending_prs: 0,
                reviewing_prs: 0,
                completed_prs: 0,
                today_prs: 0,
                avg_score: 0,
                avg_review_time: 0,
            },
            recent_prs: [],
            loading: true,
            refreshing: false,
        });
        
        this.loadDashboardData();
        this.setupBusSubscription();
        
        // Auto-refresh every 30 seconds
        this.refreshInterval = setInterval(() => this.loadDashboardData(), 30000);
    }

    willUnmount() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.busUpdate) {
            this.bus.removeEventListener("odooium_pr_update", this.busUpdate);
        }
    }

    setupBusSubscription() {
        // Subscribe to PR updates via bus
        this.busUpdate = this.onPRUpdate.bind(this);
        this.bus.addEventListener("odooium_pr_update", this.busUpdate);
    }

    onPRUpdate(event) {
        // Reload dashboard when PR is updated
        this.loadDashboardData();
    }

    async loadDashboardData() {
        try {
            this.state.refreshing = true;
            
            // Fetch stats
            const stats = await this.orm.call(
                'odooium.pull_request',
                'get_dashboard_stats',
                []
            );
            
            this.state.stats = stats;
            
            // Fetch recent PRs
            const recent_prs = await this.orm.searchRead(
                'odooium.pull_request',
                [['active', '=', True]],
                ['id', 'number', 'title', 'author', 'author_avatar', 
                 'review_status', 'ai_score', 'created_at', 'state'],
                { limit: 50, order: 'created_at desc' }
            );
            
            this.state.recent_prs = recent_prs.map(pr => ({
                ...pr,
                status_class: this.getStatusClass(pr.review_status),
                score_class: this.getScoreClass(pr.ai_score),
                severity_class: this.getSeverityClass(pr.review_status),
                icon: this.getPRIcon(pr.state),
                time_ago: this.formatTimeAgo(pr.created_at),
            }));
            
            this.state.loading = false;
            this.state.refreshing = false;
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.notification.add('Error loading dashboard data', { type: 'danger' });
            this.state.loading = false;
            this.state.refreshing = false;
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

    getSeverityClass(status) {
        const classes = {
            'pending': 'border-warning',
            'reviewing': 'border-info',
            'completed': 'border-success',
            'failed': 'border-danger',
        };
        return classes[status] || 'border-secondary';
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
        this.loadDashboardData();
    }

    onNewPr() {
        // Open repository selection or new PR form
        this.action.doActionButton({
            type: 'ir.actions.act_window',
            res_model: 'odooium.github_repository',
            views: [[false, 'tree', 'form']],
            target: 'current',
        });
    }
}

registry.category("actions").add("odooium.dashboard", OdooiumDashboard);
