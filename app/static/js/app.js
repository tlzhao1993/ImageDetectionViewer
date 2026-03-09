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

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        const activeLink = document.querySelector(`.nav-link[href="${hash}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
    }

    setupEventListeners() {
        // Load dataset button
        const loadDatasetBtn = document.getElementById('btn-load-dataset');
        if (loadDatasetBtn) {
            loadDatasetBtn.addEventListener('click', () => this.showLoadDatasetModal());
        }

        // Save to window for global access
        window.app = this;
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
        } catch (error) {
            this.showError('Error loading statistics');
        }
    }

    updateDashboard(data) {
        // TODO: Update dashboard with statistics
        console.log('Dashboard data:', data);
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
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new DetectionAnalyzer();
});
