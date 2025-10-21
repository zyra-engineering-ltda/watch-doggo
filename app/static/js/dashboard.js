// JavaScript for Service Status Monitor Dashboard

class ServiceStatusDashboard {
    constructor() {
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshIntervalMs = 300000; // 5 minutes default
        this.isRefreshing = false;

        this.init();
    }

    init() {
        console.log('Service Status Dashboard initialized');

        // Bind event handlers
        this.bindEvents();

        // Load initial data
        this.loadServiceStatuses();

        // Start auto-refresh
        this.startAutoRefresh();
    }

    bindEvents() {
        // Manual refresh button
        $('#refresh-btn').on('click', () => {
            this.manualRefresh();
        });

        // Handle page visibility changes to pause/resume auto-refresh
        $(document).on('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });

        // Handle window beforeunload to stop refresh
        $(window).on('beforeunload', () => {
            this.stopAutoRefresh();
        });

        // Add reload config button (if needed in future)
        // This could be added to admin interface
        $(document).on('keydown', (e) => {
            // Ctrl+Shift+R to reload config (for admin use)
            if (e.ctrlKey && e.shiftKey && e.key === 'R') {
                e.preventDefault();
                this.reloadConfiguration();
            }
        });
    }

    async loadServiceStatuses() {
        if (this.isRefreshing) {
            return;
        }

        this.isRefreshing = true;
        this.showLoading();

        try {
            const response = await $.ajax({
                url: '/api/status',
                method: 'GET',
                timeout: 30000
            });

            if (response.success) {
                this.updateDashboard(response.services);
                this.updateLastUpdateTime(response.timestamp);
                this.hideError();
            } else {
                this.showError(response.error || 'Failed to load service statuses');
            }

        } catch (error) {
            console.error('Error loading service statuses:', error);
            this.showError('Failed to connect to server');
        } finally {
            this.isRefreshing = false;
            this.hideLoading();
        }
    }

    async manualRefresh() {
        if (this.isRefreshing) {
            return;
        }

        console.log('Manual refresh triggered');

        // Show refresh button as loading
        const $refreshBtn = $('#refresh-btn');
        const originalHtml = $refreshBtn.html();
        $refreshBtn.html('<i class="bi bi-arrow-clockwise spin me-1"></i>Refreshing...').prop('disabled', true);

        try {
            const response = await $.ajax({
                url: '/api/refresh',
                method: 'POST',
                timeout: 60000
            });

            if (response.success) {
                this.updateDashboard(response.services);
                this.updateLastUpdateTime(response.timestamp);
                this.hideError();
            } else {
                this.showError(response.error || 'Failed to refresh service statuses');
            }

        } catch (error) {
            console.error('Error refreshing service statuses:', error);
            this.showError('Failed to refresh services');
        } finally {
            // Restore refresh button
            $refreshBtn.html(originalHtml).prop('disabled', false);
        }
    }

    updateDashboard(services) {
        const $container = $('#services-container');
        const $template = $('#service-card-template');

        // Dispose existing tooltips
        $container.find('[data-bs-toggle="tooltip"]').tooltip('dispose');

        // Clear existing cards
        $container.empty();

        // Count services by status
        const statusCounts = {
            operational: 0,
            degraded: 0,
            down: 0,
            unknown: 0
        };

        // Group services by category
        const servicesByCategory = {};
        Object.values(services).forEach(service => {
            const category = service.category || 'uncategorized';
            if (!servicesByCategory[category]) {
                servicesByCategory[category] = [];
            }
            servicesByCategory[category].push(service);

            // Update status counts
            statusCounts[service.status] = (statusCounts[service.status] || 0) + 1;
        });

        // Create category sections
        Object.keys(servicesByCategory).sort().forEach(category => {
            const categoryServices = servicesByCategory[category];
            const $categorySection = this.createCategorySection(category, categoryServices, $template);
            $container.append($categorySection);
        });

        // Initialize tooltips for new cards
        $container.find('[data-bs-toggle="tooltip"]').tooltip();

        // Update status summary
        this.updateStatusSummary(statusCounts);

        // Show services container
        $container.show();
    }

    createCategorySection(category, services, $template) {
        // Create category header
        const categoryTitle = category.charAt(0).toUpperCase() + category.slice(1);
        const $categorySection = $(`
            <div class="category-section mb-4">
                <div class="d-flex align-items-center mb-3">
                    <h4 class="category-title mb-0">${categoryTitle}</h4>
                    <span class="badge bg-secondary ms-2">${services.length}</span>
                </div>
                <div class="row g-3 category-services">
                </div>
            </div>
        `);

        const $servicesRow = $categorySection.find('.category-services');

        // Add service cards to this category
        services.forEach(service => {
            const $card = this.createServiceCard(service, $template);
            $servicesRow.append($card);
        });

        return $categorySection;
    }

    createServiceCard(service, $template) {
        const $card = $template.contents().clone();

        // Set service name
        let service_name = service.display_name ? service.display_name : service.name;
        $card.find('.service-name').text(service_name);

        // Set status icon and text
        const statusConfig = this.getStatusConfig(service.status);
        const $statusIcon = $card.find('.status-icon');
        $statusIcon.html(statusConfig.icon);
        $card.find('.service-status-text').text(statusConfig.text).addClass(statusConfig.textClass);

        // Add tooltip to status icon
        const tooltipContent = this.createTooltipContent(service);
        $statusIcon.attr({
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'data-bs-html': 'true',
            'title': tooltipContent
        });

        // Set response time
        const responseTime = service.response_time ? `${(service.response_time * 1000).toFixed(0)}ms` : '-';
        $card.find('.service-response-time').text(responseTime);

        // Set last checked time
        const lastChecked = service.last_checked ? this.formatDateTime(service.last_checked) : '-';
        $card.find('.service-last-checked').text(lastChecked);

        // Add outage duration for non-operational services
        if (service.status !== 'operational' && service.last_checked) {
            const duration = this.calculateOutageDuration(service.last_checked);
            if (duration) {
                const $durationElement = $('<div class="mt-1"><small class="text-warning d-block">Outage Duration</small><span class="text-warning fw-bold">' + duration + '</span></div>');
                $card.find('.service-details .row').after($durationElement);
            }
        }

        // Set message
        $card.find('.service-message').text(service.message || 'No message');

        // Set error if present
        if (service.error) {
            $card.find('.service-error').show();
            $card.find('.service-error-text').text(service.error);
        }

        // Set status page link if URL is available
        if (service.url) {
            $card.find('.service-link').show();
            $card.find('.service-url-link').attr('href', service.url);
        }

        // Add status class to card
        $card.find('.service-card').addClass(`status-${service.status}`);

        // Add hover effects
        $card.find('.service-card').on('mouseenter', function () {
            $(this).addClass('shadow-lg');
        }).on('mouseleave', function () {
            $(this).removeClass('shadow-lg');
        });

        return $card;
    }

    createTooltipContent(service) {
        let serviceName = service.display_name ? service.display_name : service.name;
        let content = `<strong>${serviceName}</strong><br>`;
        content += `Status: <span class="${this.getStatusConfig(service.status).textClass}">${service.status}</span><br>`;

        if (service.last_checked) {
            content += `Last Checked: ${this.formatDateTime(service.last_checked)}<br>`;

            // Calculate outage duration for non-operational services
            if (service.status !== 'operational') {
                const duration = this.calculateOutageDuration(service.last_checked);
                if (duration) {
                    content += `<span class="text-warning">Duration: ${duration}</span><br>`;
                }
            }
        }

        if (service.response_time) {
            content += `Response Time: ${(service.response_time * 1000).toFixed(0)}ms<br>`;
        }

        if (service.message) {
            content += `Message: ${service.message}<br>`;
        }

        if (service.error) {
            content += `<span class="text-danger">Error: ${service.error}</span>`;
        }

        return content;
    }

    calculateOutageDuration(lastChecked) {
        try {
            const now = new Date();
            const checkedTime = new Date(lastChecked);

            // Handle invalid or future times gracefully
            if (isNaN(checkedTime)) return "Invalid date";
            let diffMs = now - checkedTime;
            if (diffMs < 0) diffMs = 0;  // avoid negative values

            if (diffMs < 60000) { // < 1 minute
                return `${Math.floor(diffMs / 1000)}s`;
            } else if (diffMs < 3600000) { // < 1 hour
                return `${Math.floor(diffMs / 60000)}m`;
            } else if (diffMs < 86400000) { // < 1 day
                const hours = Math.floor(diffMs / 3600000);
                const minutes = Math.floor((diffMs % 3600000) / 60000);
                return `${hours}h ${minutes}m`;
            } else { // ≥ 1 day
                const days = Math.floor(diffMs / 86400000);
                const hours = Math.floor((diffMs % 86400000) / 3600000);
                return `${days}d ${hours}h`;
            }
        } catch (error) {
            console.error('Error calculating outage duration:', error);
            return null;
        }
    }


    getStatusConfig(status) {
        const configs = {
            operational: {
                icon: '<i class="bi bi-check-circle-fill text-success fs-2"></i>',
                text: 'Operational',
                textClass: 'text-success'
            },
            degraded: {
                icon: '<i class="bi bi-exclamation-triangle-fill text-warning fs-2"></i>',
                text: 'Degraded',
                textClass: 'text-warning'
            },
            down: {
                icon: '<i class="bi bi-x-circle-fill text-danger fs-2"></i>',
                text: 'Down',
                textClass: 'text-danger'
            },
            unknown: {
                icon: '<i class="bi bi-question-circle-fill text-secondary fs-2"></i>',
                text: 'Unknown',
                textClass: 'text-secondary'
            }
        };

        return configs[status] || configs.unknown;
    }

    updateStatusSummary(counts) {
        $('#operational-count').text(counts.operational || 0);
        $('#degraded-count').text(counts.degraded || 0);
        $('#down-count').text(counts.down || 0);
        $('#unknown-count').text(counts.unknown || 0);
    }

    updateLastUpdateTime(timestamp) {
        const formattedTime = this.formatDateTime(timestamp);
        $('#last-update-time').text(formattedTime);
    }

    formatDateTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString();
    }

    showLoading() {
        $('#loading-indicator').show();
        $('#services-container').hide();
        $('#error-alert').addClass('d-none');

        // Add pulse animation to existing cards if they exist
        $('.service-card').addClass('loading-pulse');
    }

    hideLoading() {
        $('#loading-indicator').hide();
        $('.service-card').removeClass('loading-pulse');
    }

    showError(message) {
        $('#error-message').text(message);
        $('#error-alert').removeClass('d-none');
    }

    hideError() {
        $('#error-alert').addClass('d-none');
    }

    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        if (this.autoRefreshEnabled && !document.hidden) {
            this.refreshInterval = setInterval(() => {
                this.loadServiceStatuses();
            }, this.refreshIntervalMs);

            console.log(`Auto-refresh started with ${this.refreshIntervalMs / 1000}s interval`);
        }
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('Auto-refresh stopped');
        }
    }

    setRefreshInterval(intervalMs) {
        this.refreshIntervalMs = intervalMs;
        if (this.autoRefreshEnabled) {
            this.startAutoRefresh();
        }
    }

    async reloadConfiguration() {
        console.log('Reloading configuration...');

        try {
            const response = await $.ajax({
                url: '/api/config/reload',
                method: 'POST',
                timeout: 30000
            });

            if (response.success) {
                console.log('Configuration reloaded successfully');

                // Update refresh interval if it changed
                if (response.refresh_interval) {
                    this.setRefreshInterval(response.refresh_interval * 1000);
                }

                // Force refresh of service statuses
                await this.loadServiceStatuses();

                // Show success message (could be enhanced with toast notifications)
                this.showTemporaryMessage('Configuration reloaded successfully', 'success');

            } else {
                console.error('Failed to reload configuration:', response.error);
                this.showTemporaryMessage('Failed to reload configuration: ' + response.error, 'error');
            }

        } catch (error) {
            console.error('Error reloading configuration:', error);
            this.showTemporaryMessage('Error reloading configuration', 'error');
        }
    }

    showTemporaryMessage(message, type = 'info') {
        // Create temporary alert
        const alertClass = type === 'success' ? 'alert-success' :
            type === 'error' ? 'alert-danger' : 'alert-info';

        const $alert = $(`
            <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
                <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);

        $('body').append($alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            $alert.alert('close');
        }, 5000);
    }
}

// Initialize dashboard when document is ready
$(document).ready(function () {
    window.dashboard = new ServiceStatusDashboard();
});