// Image Detection Result Analyzer - Main Application Script

class DetectionAnalyzer {
    constructor() {
        this.datasetId = null;
        this.currentImageId = null;
        this.iouThreshold = 0.5;
        this.confidenceThreshold = 0.5;
        this.filters = {
            classes: [],
            status: 'all'
        };

        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.setupSliderTrackFill();
        this.handleHashChange();
        window.addEventListener('hashchange', () => this.handleHashChange());
    }

    setupNavigation() {
        // Handle hash-based routing
        window.addEventListener('hashchange', () => {
            this.handleHashChange();
        });
    }

    handleHashChange() {
        const hash = window.location.hash || '#dashboard';

        // Hide all pages
        this.hideAllPages();

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`.nav-link[href="${hash}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }

        // Show the appropriate page
        if (hash === '#dashboard') {
            this.showDashboard();
        } else if (hash === '#comparison') {
            // TODO: Implement comparison view
            console.log('Comparison view');
        }
    }

    hideAllPages() {
        // Hide all page containers
        const pages = document.querySelectorAll('.page');
        pages.forEach(page => {
            page.style.display = 'none';
        });
    }

    showDashboard() {
        const dashboardPage = document.getElementById('dashboard-page');
        const emptyState = document.getElementById('dashboard-empty-state');

        if (dashboardPage && emptyState) {
            if (this.datasetId) {
                dashboardPage.style.display = 'block';
                emptyState.style.display = 'none';
            } else {
                dashboardPage.style.display = 'none';
                emptyState.style.display = 'block';
            }
        }

        // Load statistics if dataset is loaded
        if (this.datasetId) {
            this.loadStatistics();
        }
    }

    setupEventListeners() {
        // Load dataset button (navbar)
        const loadDatasetBtn = document.getElementById('btn-load-dataset');
        if (loadDatasetBtn) {
            loadDatasetBtn.addEventListener('click', () => this.showLoadDatasetModal());
        }

        // Load dataset button (empty state)
        const emptyLoadDatasetBtn = document.getElementById('empty-load-dataset');
        if (emptyLoadDatasetBtn) {
            emptyLoadDatasetBtn.addEventListener('click', () => this.showLoadDatasetModal());
        }

        // IoU threshold slider
        const iouSlider = document.getElementById('iou-threshold');
        if (iouSlider) {
            iouSlider.addEventListener('input', (e) => {
                this.iouThreshold = parseFloat(e.target.value);
                document.getElementById('iou-threshold-value').textContent = this.iouThreshold.toFixed(1);
                this.updateSliderTrackFill(iouSlider);
            });
            iouSlider.addEventListener('change', () => {
                this.recalculateStatistics();
            });
        }

        // Confidence threshold slider
        const confidenceSlider = document.getElementById('confidence-threshold');
        if (confidenceSlider) {
            confidenceSlider.addEventListener('input', (e) => {
                this.confidenceThreshold = parseFloat(e.target.value);
                document.getElementById('confidence-threshold-value').textContent = this.confidenceThreshold.toFixed(2);
                this.updateSliderTrackFill(confidenceSlider);
            });
            confidenceSlider.addEventListener('change', () => {
                this.recalculateStatistics();
            });
        }

        // Class search input
        const classSearch = document.getElementById('class-search');
        if (classSearch) {
            classSearch.addEventListener('input', (e) => {
                this.filterMetricsTable(e.target.value);
            });
        }

        // Setup sortable table headers
        this.setupSortableTableHeaders();

        // Export buttons
        const exportCsvBtn = document.getElementById('export-csv');
        if (exportCsvBtn) {
            exportCsvBtn.addEventListener('click', () => this.exportStatistics('csv'));
        }

        const exportJsonBtn = document.getElementById('export-json');
        if (exportJsonBtn) {
            exportJsonBtn.addEventListener('click', () => this.exportStatistics('json'));
        }

        // Save to window for global access
        window.app = this;
    }

    setupSliderTrackFill() {
        // Initialize track fill for all sliders
        const sliders = document.querySelectorAll('.form-range');
        sliders.forEach(slider => {
            this.updateSliderTrackFill(slider);
        });
    }

    setupSortableTableHeaders() {
        // Store current sort state
        this.currentSort = {
            column: null,
            direction: 'asc'
        };

        // Get all sortable headers
        const sortableHeaders = document.querySelectorAll('th.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortColumn = header.getAttribute('data-sort');
                const sortType = header.getAttribute('data-type');

                // Toggle sort direction if clicking same column
                if (this.currentSort.column === sortColumn) {
                    this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    this.currentSort.column = sortColumn;
                    this.currentSort.direction = 'asc';
                }

                // Update sort icons
                this.updateSortIcons();

                // Sort the table
                this.sortMetricsTable(sortColumn, sortType, this.currentSort.direction);
            });
        });
    }

    updateSortIcons() {
        // Clear all sort icons
        const allIcons = document.querySelectorAll('.sort-icon');
        allIcons.forEach(icon => {
            icon.innerHTML = '';
        });

        // Set icon for current sort column
        if (this.currentSort.column) {
            const header = document.querySelector(`th[data-sort="${this.currentSort.column}"]`);
            if (header) {
                const icon = header.querySelector('.sort-icon');
                if (icon) {
                    icon.innerHTML = this.currentSort.direction === 'asc' ? '&#9650;' : '&#9660;'; // Up or down arrow
                }
            }
        }
    }

    sortMetricsTable(column, type, direction) {
        const tableBody = document.getElementById('metrics-table-body');
        if (!tableBody) return;

        const rows = Array.from(tableBody.querySelectorAll('tr'));

        // Get column index
        const headerIndex = this.getColumnIndex(column);
        if (headerIndex === -1) return;

        // Sort rows
        rows.sort((rowA, rowB) => {
            const cellA = rowA.cells[headerIndex];
            const cellB = rowB.cells[headerIndex];

            if (!cellA || !cellB) return 0;

            let valueA, valueB;

            if (type === 'string') {
                valueA = cellA.textContent.trim().toLowerCase();
                valueB = cellB.textContent.trim().toLowerCase();
            } else {
                // For numeric values, remove formatting and parse
                valueA = parseFloat(cellA.textContent.replace(/[^\d.-]/g, '')) || 0;
                valueB = parseFloat(cellB.textContent.replace(/[^\d.-]/g, '')) || 0;
            }

            if (valueA < valueB) return direction === 'asc' ? -1 : 1;
            if (valueA > valueB) return direction === 'asc' ? 1 : -1;
            return 0;
        });

        // Reorder rows in the table
        rows.forEach(row => {
            tableBody.appendChild(row);
        });
    }

    getColumnIndex(columnName) {
        const headers = document.querySelectorAll('th[data-sort]');
        for (let i = 0; i < headers.length; i++) {
            if (headers[i].getAttribute('data-sort') === columnName) {
                return i;
            }
        }
        return -1;
    }

    updateSliderTrackFill(slider) {
        // Calculate the percentage of the slider value
        const min = parseFloat(slider.min) || 0;
        const max = parseFloat(slider.max) || 1;
        const value = parseFloat(slider.value) || 0;
        const percentage = ((value - min) / (max - min)) * 100;

        // Update the background gradient for track fill effect
        const primaryColor = '#2c5282';
        const trackColor = '#e2e8f0';
        slider.style.background = `linear-gradient(to right, ${primaryColor} 0%, ${primaryColor} ${percentage}%, ${trackColor} ${percentage}%, ${trackColor} 100%)`;
    }

    showLoadDatasetModal() {
        // TODO: Implement load dataset modal
        console.log('Load dataset modal');
    }

    async loadDataset(path) {
        try {
            this.showLoading();

            const response = await fetch('/api/dataset/load', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dataset_path: path,
                    iou_threshold: this.iouThreshold
                })
            });

            const data = await response.json();

            if (data.success) {
                this.datasetId = data.dataset_id;
                window.location.hash = '#dashboard';
                await this.loadStatistics();
            } else {
                this.showError('Failed to load dataset');
            }
        } catch (error) {
            this.showError('Error loading dataset: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch(`/api/statistics/${this.datasetId}`);
            const data = await response.json();
            this.updateDashboard(data);
            // Update dashboard display state
            this.showDashboard();
        } catch (error) {
            this.showError('Error loading statistics');
        }
    }

    updateDashboard(data) {
        // Update summary cards
        if (data.overall_metrics) {
            document.getElementById('summary-total-images').textContent = data.overall_metrics.total_gt_boxes || '-';
            document.getElementById('summary-total-classes').textContent = data.classes?.length || '-';
            document.getElementById('summary-avg-recall').textContent = data.overall_metrics.recall !== undefined ? data.overall_metrics.recall.toFixed(3) : '-';
            document.getElementById('summary-avg-precision').textContent = data.overall_metrics.precision !== undefined ? data.overall_metrics.precision.toFixed(3) : '-';
        }

        // Update metrics table
        this.updateMetricsTable(data.classes || []);

        // Update charts
        this.updateCharts(data.classes || []);
    }

    updateMetricsTable(classes) {
        const tableBody = document.getElementById('metrics-table-body');
        if (!tableBody) return;

        if (classes.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No data available.</td></tr>';
            return;
        }

        tableBody.innerHTML = classes.map(cls => `
            <tr>
                <td><strong>${this.escapeHtml(cls.name)}</strong></td>
                <td>${cls.total_gt_count || 0}</td>
                <td>${cls.total_pred_count || 0}</td>
                <td>${cls.tp_count || 0}</td>
                <td>${cls.fp_count || 0}</td>
                <td>${cls.fn_count || 0}</td>
                <td>${cls.recall !== undefined ? cls.recall.toFixed(3) : '-'}</td>
                <td>${cls.precision !== undefined ? cls.precision.toFixed(3) : '-'}</td>
                <td>${cls.fpr !== undefined ? cls.fpr.toFixed(3) : '-'}</td>
                <td>${cls.f1_score !== undefined ? cls.f1_score.toFixed(3) : '-'}</td>
            </tr>
        `).join('');
    }

    updateCharts(classes) {
        if (classes.length === 0) return;

        const labels = classes.map(cls => cls.name);
        const recallData = classes.map(cls => cls.recall !== undefined ? cls.recall : 0);
        const precisionData = classes.map(cls => cls.precision !== undefined ? cls.precision : 0);
        const fprData = classes.map(cls => cls.fpr !== undefined ? cls.fpr : 0);

        // Generate colors for each class
        const colors = this.generateColors(classes.length);

        // Update recall chart
        this.createOrUpdateChart('recall-chart', 'Recall', labels, recallData, colors);

        // Update precision chart
        this.createOrUpdateChart('precision-chart', 'Precision', labels, precisionData, colors);

        // Update FPR chart
        this.createOrUpdateChart('fpr-chart', 'False Positive Rate', labels, fprData, colors);
    }

    createOrUpdateChart(canvasId, label, labels, data, colors) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Set canvas height explicitly for Chart.js to render properly
        canvas.style.height = '300px';
        canvas.style.width = '100%';

        const ctx = canvas.getContext('2d');

        // Check if chart already exists and destroy it
        if (canvas.chart) {
            canvas.chart.destroy();
        }

        // Create new chart with enhanced tooltip configuration
        canvas.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: data,
                    backgroundColor: colors.map(c => c.background),
                    borderColor: colors.map(c => c.border),
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 6,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`;
                            },
                            title: function(context) {
                                return context[0].label;
                            }
                        }
                    }
                }
            }
        });
    }

    generateColors(count) {
        const colors = [];
        const baseHues = [210, 150, 45, 0, 270, 180, 300, 330, 30, 60]; // Blue, green, orange, red, purple, cyan, magenta, pink, brown, yellow

        for (let i = 0; i < count; i++) {
            const hue = baseHues[i % baseHues.length];
            const saturation = 70;
            const lightness = 50;
            colors.push({
                background: `hsla(${hue}, ${saturation}%, ${lightness}%, 0.7)`,
                border: `hsla(${hue}, ${saturation}%, ${lightness - 10}%, 1)`
            });
        }

        return colors;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading() {
        const overlay = document.getElementById('loading-overlay') || this.createLoadingOverlay();
        overlay.classList.remove('d-none');
    }

    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('d-none');
        }
    }

    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(overlay);
        return overlay;
    }

    showError(message) {
        alert(message); // TODO: Implement proper error modal
    }

    async recalculateStatistics() {
        if (!this.datasetId) return;

        try {
            this.showLoading();

            const response = await fetch('/api/statistics/recalculate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dataset_id: this.datasetId,
                    iou_threshold: this.iouThreshold,
                    confidence_threshold: this.confidenceThreshold
                })
            });

            const data = await response.json();

            if (data.success) {
                await this.loadStatistics();
            } else {
                this.showError('Failed to recalculate statistics');
            }
        } catch (error) {
            this.showError('Error recalculating statistics: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    filterMetricsTable(searchTerm) {
        const tableBody = document.getElementById('metrics-table-body');
        if (!tableBody) return;

        const rows = tableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const classNameCell = row.querySelector('td:first-child');
            if (classNameCell) {
                const className = classNameCell.textContent.toLowerCase();
                if (className.includes(searchTerm.toLowerCase())) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });
    }

    async exportStatistics(format) {
        if (!this.datasetId) {
            this.showError('No dataset loaded');
            return;
        }

        try {
            const response = await fetch(`/api/statistics/export/${this.datasetId}?format=${format}`);

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `statistics_dataset_${this.datasetId}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const errorData = await response.json();
                this.showError(errorData.error || 'Failed to export statistics');
            }
        } catch (error) {
            this.showError('Error exporting statistics: ' + error.message);
        }
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DetectionAnalyzer();
});
