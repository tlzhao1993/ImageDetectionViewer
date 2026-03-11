// Image Detection Result Analyzer - Main Application Script

class DetectionAnalyzer {
    constructor() {
        this.datasetId = null;
        this.currentImageId = null;
        this.iouThreshold = 0.5;
        this.confidenceThreshold = 0.5;
        this.filters = {
            search: '',
            classFilter: '',
            statusFilter: ''
        };
        this.allClasses = [];
        this.statisticsLoaded = false; // Track if statistics are already loaded

        // Box visibility toggles
        this.showGTBoxes = true;
        this.showPredBoxes = true;
        this.showLabels = true;
        this.currentImageData = null; // Store current image data for re-rendering
        this.cachedImage = null; // Cache loaded Image object to avoid re-loading during drag

        // Zoom and pan state
        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;

        // Image list pagination state
        this.currentPage = 1;
        this.perPage = 50; // Images per page
        this.totalImages = 0;
        this.totalPages = 1;

        this.init();
    }

    async init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.setupSliderTrackFill();
        await this.restoreCurrentDataset();
        this.handleHashChange();
    }

    async restoreCurrentDataset() {
        try {
            const response = await fetch('/api/dataset/current');
            const data = await response.json();
            if (data.dataset_id) {
                this.datasetId = data.dataset_id;
                console.log('Restored dataset ID:', this.datasetId);
            }
        } catch (error) {
            console.error('Error restoring dataset ID:', error);
        }
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
            link.removeAttribute('aria-current');
        });

        const activeLink = document.querySelector(`.nav-link[href="${hash}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
            activeLink.setAttribute('aria-current', 'page');
        }

        // Show the appropriate page
        if (hash === '#dashboard') {
            this.showDashboard();
        } else if (hash === '#comparison') {
            this.showComparisonView();
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
        const comparisonEmptyState = document.getElementById('comparison-empty-state');

        if (dashboardPage && emptyState) {
            if (this.datasetId) {
                dashboardPage.style.display = 'block';
                emptyState.style.display = 'none';
            } else {
                dashboardPage.style.display = 'none';
                emptyState.style.display = 'block';
            }
        }

        // Hide comparison empty state
        if (comparisonEmptyState) {
            comparisonEmptyState.style.display = 'none';
        }

        // Load statistics if dataset is loaded and not already loaded
        if (this.datasetId && !this.statisticsLoaded) {
            this.loadStatistics();
        }
    }

    showComparisonView() {
        const comparisonPage = document.getElementById('comparison-page');
        const emptyState = document.getElementById('comparison-empty-state');
        const dashboardEmptyState = document.getElementById('dashboard-empty-state');

        if (comparisonPage && emptyState) {
            if (this.datasetId) {
                comparisonPage.style.display = 'block';
                emptyState.style.display = 'none';
                // Load classes for filter
                this.loadClassesForFilter();
                // Load images list
                this.loadImagesList();
            } else {
                comparisonPage.style.display = 'none';
                emptyState.style.display = 'block';
            }
        }

        // Hide dashboard empty state
        if (dashboardEmptyState) {
            dashboardEmptyState.style.display = 'none';
        }
    }

    async loadClassesForFilter() {
        if (!this.datasetId) return;

        try {
            const response = await fetch(`/api/statistics/${this.datasetId}`);
            const data = await response.json();

            if (data.success && data.classes) {
                this.allClasses = data.classes;
                this.updateClassFilterDropdown();
            }
        } catch (error) {
            console.error('Error loading classes for filter:', error);
        }
    }

    updateClassFilterDropdown() {
        const classFilter = document.getElementById('class-filter');
        if (!classFilter) return;

        // Clear existing options except the first one
        while (classFilter.options.length > 1) {
            classFilter.remove(1);
        }

        // Add class options
        this.allClasses.forEach(cls => {
            const option = document.createElement('option');
            option.value = cls.name;
            option.textContent = cls.name;
            classFilter.appendChild(option);
        });
    }

    async loadImagesList(resetPage = true) {
        if (!this.datasetId) return;

        // Reset to page 1 if requested (e.g., when filters change)
        if (resetPage) {
            this.currentPage = 1;
        }

        try {
            // Build URL with filter parameters (class and status filters are server-side)
            let url = `/api/images/${this.datasetId}?page=${this.currentPage}&per_page=${this.perPage}`;

            if (this.filters.classFilter) {
                url += `&class_filter=${encodeURIComponent(this.filters.classFilter)}`;
            }

            if (this.filters.statusFilter) {
                url += `&status_filter=${encodeURIComponent(this.filters.statusFilter)}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (data.images) {
                this.allImages = data.images;
                this.totalImages = data.total;
                this.totalPages = data.total_pages;
                this.applyClientSideFilters();
                this.updatePaginationControls();
            }
        } catch (error) {
            console.error('Error loading images list:', error);
            const container = document.getElementById('image-list-container');
            if (container) {
                container.innerHTML = '<div class="text-center text-danger py-5">Failed to load images</div>';
            }
        }
    }

    applyClientSideFilters() {
        if (!this.allImages) return;

        let filteredImages = [...this.allImages];

        // Apply search filter (client-side)
        if (this.filters.search) {
            const searchTerm = this.filters.search.toLowerCase();
            filteredImages = filteredImages.filter(image =>
                image.filename.toLowerCase().includes(searchTerm)
            );
        }

        // Render filtered images
        this.renderImagesList(filteredImages);
    }

    renderImagesList(images) {
        const container = document.getElementById('image-list-container');
        if (!container) return;

        if (!images || images.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-5">No images found</div>';
            // Hide pagination controls
            const pagination = document.getElementById('pagination-controls');
            if (pagination) pagination.style.display = 'none';
            return;
        }

        container.innerHTML = images.map(image => {
            const statusClass = image.is_perfect ? 'status-perfect' : (image.has_fp || image.has_fn ? 'status-warning' : 'status-perfect');
            return `
                <div class="image-list-item" data-image-id="${image.id}" tabindex="0" role="button" aria-label="${this.escapeHtml(image.filename)}">
                    <img src="${image.thumbnail_path || ''}" alt="${this.escapeHtml(image.filename)}" class="thumbnail" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2260%22 height=%2260%22%3E%3Crect fill=%22%23e2e8f0%22 width=%22100%25%22 height=%22100%25%22/%3E%3Ctext fill=%22%2394a3b8%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3E%3F%3C/text%3E%3C/svg%3E'">
                    <div class="image-info">
                        <div class="filename">${this.escapeHtml(image.filename)}</div>
                        <div class="image-stats">
                            GT: ${image.total_gt_boxes} | Pred: ${image.total_pred_boxes}
                        </div>
                    </div>
                    <span class="status-dot ${statusClass}" title="${image.is_perfect ? 'Perfect' : (image.has_fp || image.has_fn ? 'Has errors' : 'Good')}"></span>
                </div>
            `;
        }).join('');

        // Add event listeners to image list items
        container.querySelectorAll('.image-list-item').forEach(item => {
            // Click event
            item.addEventListener('click', () => {
                const imageId = parseInt(item.getAttribute('data-image-id'));
                this.selectImage(imageId);
            });

            // Focus event - update active state
            item.addEventListener('focus', () => {
                this.updateActiveStateOnFocus(item);
            });

            // Keydown event for keyboard navigation
            item.addEventListener('keydown', (e) => {
                this.handleImageListKeydown(e, item);
            });
        });

        // Show pagination controls
        const pagination = document.getElementById('pagination-controls');
        if (pagination) pagination.style.display = 'flex';
    }

    updateImagesList(images) {
        // Store images and apply client-side filters
        this.allImages = images;
        this.applyClientSideFilters();
    }

    updatePaginationControls() {
        const paginationContainer = document.getElementById('pagination-controls');
        if (!paginationContainer) return;

        const hasPrev = this.currentPage > 1;
        const hasNext = this.currentPage < this.totalPages;

        // Build pagination HTML
        let html = `
            <div class="pagination-info">
                Showing ${((this.currentPage - 1) * this.perPage + 1)} - ${Math.min(this.currentPage * this.perPage, this.totalImages)} of ${this.totalImages} images
                (Page ${this.currentPage} of ${this.totalPages})
            </div>
            <div class="pagination-buttons">
                <button class="btn btn-sm ${hasPrev ? 'btn-primary' : 'btn-secondary'}"
                        id="prev-page-btn"
                        ${!hasPrev ? 'disabled' : ''}
                        aria-label="Previous page">
                    <i class="fas fa-chevron-left me-1" aria-hidden="true"></i>Previous
                </button>
                <button class="btn btn-sm ${hasNext ? 'btn-primary' : 'btn-secondary'}"
                        id="next-page-btn"
                        ${!hasNext ? 'disabled' : ''}
                        aria-label="Next page">
                    Next<i class="fas fa-chevron-right ms-1" aria-hidden="true"></i>
                </button>
            </div>
        `;

        paginationContainer.innerHTML = html;

        // Add event listeners
        const prevBtn = document.getElementById('prev-page-btn');
        const nextBtn = document.getElementById('next-page-btn');

        if (prevBtn && hasPrev) {
            prevBtn.addEventListener('click', () => this.goToPreviousPage());
        }
        if (nextBtn && hasNext) {
            nextBtn.addEventListener('click', () => this.goToNextPage());
        }
    }

    goToPreviousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadImagesList(false);
        }
    }

    goToNextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadImagesList(false);
        }
    }

    updateImagesList(images) {
        const container = document.getElementById('image-list-container');
        if (!container) return;

        if (!images || images.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-5">No images found</div>';
            return;
        }

        // Store all images for client-side filtering
        this.allImages = images;

        // Apply client-side search filter (if needed)
        let filteredImages = images;
        if (this.filters.search) {
            const searchTerm = this.filters.search.toLowerCase();
            filteredImages = images.filter(image =>
                image.filename.toLowerCase().includes(searchTerm)
            );
        }

        // Update container with filtered images
        if (filteredImages.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-5">No images match your search criteria</div>';
            return;
        }

        container.innerHTML = filteredImages.map(image => {
            const statusClass = image.is_perfect ? 'status-perfect' : (image.has_fp || image.has_fn ? 'status-warning' : 'status-perfect');
            return `
                <div class="image-list-item" data-image-id="${image.id}" tabindex="0" role="button" aria-label="${this.escapeHtml(image.filename)}">
                    <img src="${image.thumbnail_path || ''}" alt="${this.escapeHtml(image.filename)}" class="thumbnail" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2260%22 height=%2260%22%3E%3Crect fill=%22%23e2e8f0%22 width=%22100%25%22 height=%22100%25%22/%3E%3Ctext fill=%22%2394a3b8%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3E%3F%3C/text%3E%3C/svg%3E'">
                    <div class="image-info">
                        <div class="filename">${this.escapeHtml(image.filename)}</div>
                        <div class="image-stats">
                            GT: ${image.total_gt_boxes} | Pred: ${image.total_pred_boxes}
                        </div>
                    </div>
                    <span class="status-dot ${statusClass}" title="${image.is_perfect ? 'Perfect' : (image.has_fp || image.has_fn ? 'Has errors' : 'Good')}"></span>
                </div>
            `;
        }).join('');

        // Add event listeners to image list items
        container.querySelectorAll('.image-list-item').forEach(item => {
            // Click event
            item.addEventListener('click', () => {
                const imageId = parseInt(item.getAttribute('data-image-id'));
                this.selectImage(imageId);
            });

            // Focus event - update active state
            item.addEventListener('focus', () => {
                this.updateActiveStateOnFocus(item);
            });

            // Keydown event for keyboard navigation
            item.addEventListener('keydown', (e) => {
                this.handleImageListKeydown(e, item);
            });
        });
    }

    async selectImage(imageId) {
        if (!this.datasetId) return;

        this.currentImageId = imageId;

        // Update active state in list
        document.querySelectorAll('.image-list-item').forEach(item => {
            item.classList.remove('active');
            if (parseInt(item.getAttribute('data-image-id')) === imageId) {
                item.classList.add('active');
            }
        });

        // Load image details
        await this.loadImageDetail(imageId);
    }

    updateActiveStateOnFocus(item) {
        // Remove active state from all items
        document.querySelectorAll('.image-list-item').forEach(el => {
            el.classList.remove('active');
        });
        // Add active state to focused item
        item.classList.add('active');
    }

    handleImageListKeydown(e, currentItem) {
        const items = Array.from(document.querySelectorAll('.image-list-item'));
        const currentIndex = items.indexOf(currentItem);

        switch (e.key) {
            case 'Enter':
            case ' ':
                // Select the currently focused image
                e.preventDefault();
                const imageId = parseInt(currentItem.getAttribute('data-image-id'));
                this.selectImage(imageId);
                break;

            case 'ArrowDown':
                // Move to next item
                e.preventDefault();
                if (currentIndex < items.length - 1) {
                    items[currentIndex + 1].focus();
                }
                break;

            case 'ArrowUp':
                // Move to previous item
                e.preventDefault();
                if (currentIndex > 0) {
                    items[currentIndex - 1].focus();
                }
                break;

            case 'ArrowRight':
            case 'ArrowLeft':
                // Allow arrow keys to navigate between images when image view is focused
                // Only if image is already selected
                if (this.currentImageId && currentIndex !== -1) {
                    e.preventDefault();
                    const direction = e.key === 'ArrowRight' ? 1 : -1;
                    this.navigateImage(direction);
                }
                break;
        }
    }

    async loadImageDetail(imageId) {
        if (!this.datasetId) return;

        const detailContent = document.getElementById('image-detail-content');
        if (detailContent) {
            detailContent.innerHTML = '<div class="text-center py-5" role="status" aria-live="polite"><i class="fas fa-spinner fa-spin fa-2x mb-3" aria-hidden="true"></i><p>Loading image details...</p></div>';
        }

        try {
            const response = await fetch(`/api/images/${this.datasetId}/${imageId}`);
            const data = await response.json();

            if (data.success) {
                this.updateImageDetail(data);
            }
        } catch (error) {
            console.error('Error loading image detail:', error);
            if (detailContent) {
                detailContent.innerHTML = '<div class="text-center text-danger py-5">Failed to load image details</div>';
            }
        }
    }

    updateImageDetail(data) {
        const detailContent = document.getElementById('image-detail-content');
        if (!detailContent) return;

        // Calculate total boxes
        const totalGT = data.ground_truth_boxes ? data.ground_truth_boxes.length : 0;
        const totalPred = data.prediction_boxes ? data.prediction_boxes.length : 0;

        // Build per-class stats table rows
        const classStatsRows = Object.entries(data.per_class_stats || {}).map(([className, stats]) => `
            <tr>
                <td>${this.escapeHtml(className)}</td>
                <td class="text-center">${stats.gt_count || 0}</td>
                <td class="text-center">${stats.pred_count || 0}</td>
                <td class="text-center">${stats.tp || 0}</td>
                <td class="text-center">${stats.fp || 0}</td>
                <td class="text-center">${stats.fn || 0}</td>
            </tr>
        `).join('');

        detailContent.innerHTML = `
            <div class="image-header-section">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <h5 class="mb-1"><i class="fas fa-image me-2" aria-hidden="true"></i>${this.escapeHtml(data.filename)}</h5>
                        <p class="mb-0 text-muted">
                            <small>${data.dimensions ? `${data.dimensions.width} x ${data.dimensions.height} pixels` : ''}</small>
                        </p>
                    </div>
                    <div class="d-flex gap-2" role="group" aria-label="Image navigation">
                        <button class="btn btn-outline-primary btn-sm" id="prev-image-btn" aria-label="Previous image">
                            <i class="fas fa-chevron-left me-1" aria-hidden="true"></i> Previous
                        </button>
                        <button class="btn btn-outline-primary btn-sm" id="next-image-btn" aria-label="Next image">
                            Next <i class="fas fa-chevron-right ms-1" aria-hidden="true"></i>
                        </button>
                    </div>
                </div>
                <div class="d-flex gap-3">
                    <span class="badge bg-primary">GT: ${totalGT}</span>
                    <span class="badge bg-info">Pred: ${totalPred}</span>
                </div>

                <!-- Box Visibility Toggles -->
                <div class="d-flex gap-2 mb-3 mt-3">
                    <button class="btn btn-sm toggle-btn active" id="toggle-gt-boxes" title="Show/Hide Ground Truth Boxes"
                            aria-label="Toggle Ground Truth Boxes" aria-pressed="true">
                        <i class="fas fa-check-square me-1" aria-hidden="true"></i> GT Boxes
                    </button>
                    <button class="btn btn-sm toggle-btn active" id="toggle-pred-boxes" title="Show/Hide Prediction Boxes"
                            aria-label="Toggle Prediction Boxes" aria-pressed="true">
                        <i class="fas fa-crosshairs me-1" aria-hidden="true"></i> Pred Boxes
                    </button>
                    <button class="btn btn-sm toggle-btn active" id="toggle-labels" title="Show/Hide Labels"
                            aria-label="Toggle Labels" aria-pressed="true">
                        <i class="fas fa-tag me-1" aria-hidden="true"></i> Labels
                    </button>
                </div>

                <!-- Zoom Controls -->
                <div class="d-flex gap-2 mb-3" role="group" aria-label="Zoom controls">
                    <button class="btn btn-sm zoom-btn" id="zoom-out" title="Zoom Out"
                            aria-label="Zoom out">
                        <i class="fas fa-search-minus" aria-hidden="true"></i>
                    </button>
                    <button class="btn btn-sm zoom-btn" id="zoom-reset" title="Reset Zoom"
                            aria-label="Reset zoom to 100%">
                        <span id="zoom-level-display">100%</span>
                    </button>
                    <button class="btn btn-sm zoom-btn" id="zoom-in" title="Zoom In"
                            aria-label="Zoom in">
                        <i class="fas fa-search-plus" aria-hidden="true"></i>
                    </button>
                </div>
            </div>

            <div class="image-display-section">
                <div class="card">
                    <div class="card-body p-0">
                        <div class="canvas-container" id="canvas-container">
                            <canvas id="image-canvas"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <div class="image-statistics-section">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-chart-bar me-2" aria-hidden="true"></i>Per-Image Statistics</h6>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-bordered table-striped">
                                <thead class="table-light">
                                    <tr>
                                        <th>Class</th>
                                        <th class="text-center">GT</th>
                                        <th class="text-center">Pred</th>
                                        <th class="text-center">TP</th>
                                        <th class="text-center">FP</th>
                                        <th class="text-center">FN</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${classStatsRows || '<tr><td colspan="6" class="text-center text-muted">No statistics available</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add event listeners for navigation buttons
        const prevBtn = document.getElementById('prev-image-btn');
        const nextBtn = document.getElementById('next-image-btn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.navigateImage(-1));
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.navigateImage(1));
        }

        // Store current image data for re-rendering
        this.currentImageData = data;
        // Clear cached image when loading a new image (different path)
        if (this.cachedImage && this.cachedImage.src !== data.image_path) {
            this.cachedImage = null;
        }

        // Render image with bounding boxes
        this.renderImageWithBoundingBoxes(data);

        // Add event listeners for toggle buttons
        this.setupToggleButtons();

        // Add event listeners for zoom controls
        this.setupZoomControls();

        // Add event listeners for pan/drag functionality
        this.setupPanDrag();
    }

    renderConfidenceDistribution(predictionBoxes) {
        const canvas = document.getElementById('confidence-distribution-chart');
        if (!canvas) return;

        // Extract confidence scores from prediction boxes
        const confidenceScores = predictionBoxes
            .map(box => box.confidence)
            .filter(score => score !== undefined && score !== null);

        if (confidenceScores.length === 0) return;

        // Set canvas dimensions
        canvas.style.height = '250px';
        canvas.style.width = '100%';

        const ctx = canvas.getContext('2d');

        // Destroy existing chart if present
        if (canvas.chart) {
            canvas.chart.destroy();
        }

        // Create histogram bins (10 bins from 0 to 1)
        const binCount = 10;
        const bins = new Array(binCount).fill(0);
        const binLabels = [];

        for (let i = 0; i < binCount; i++) {
            const binStart = i / binCount;
            const binEnd = (i + 1) / binCount;
            binLabels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);
        }

        // Populate bins
        confidenceScores.forEach(score => {
            const binIndex = Math.min(Math.floor(score * binCount), binCount - 1);
            bins[binIndex]++;
        });

        // Generate colors for bins based on confidence level
        const backgroundColors = bins.map((_, i) => {
            const hue = (i / binCount) * 120; // Red (0) to Green (120)
            return `hsla(${hue}, 70%, 50%, 0.7)`;
        });

        const borderColors = bins.map((_, i) => {
            const hue = (i / binCount) * 120;
            return `hsla(${hue}, 70%, 40%, 1)`;
        });

        // Create the chart
        canvas.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: binLabels,
                datasets: [{
                    label: 'Number of Predictions',
                    data: bins,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Confidence Score Range'
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
                            title: function(context) {
                                return `Confidence: ${context[0].label}`;
                            },
                            label: function(context) {
                                return `Predictions: ${context.parsed.y}`;
                            }
                        }
                    }
                }
            }
        });
    }

    renderImageWithBoundingBoxes(data) {
        const canvas = document.getElementById('image-canvas');
        const ctx = canvas.getContext('2d');
        if (!canvas || !ctx) return;

        const container = canvas.parentElement;
        const containerWidth = container.clientWidth;
        const containerHeight = container.clientHeight;

        const imageWidth = data.dimensions?.width || 800;
        const imageHeight = data.dimensions?.height || 600;

        // Calculate scale to fit the container while maintaining aspect ratio
        const scaleX = containerWidth / imageWidth * 0.98;
        const scaleY = containerHeight / imageHeight * 0.98;

        // Use the smaller scale to ensure the entire image fits within the container
        const baseScale = Math.min(scaleX, scaleY);

        // Set canvas size to fill the container
        canvas.width = containerWidth;
        canvas.height = containerHeight;

        // Store the base scale for zoom calculations
        this.baseScale = baseScale;
        this.currentImageWidth = imageWidth;
        this.currentImageHeight = imageHeight;

        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Calculate centered position
        const scaledImageWidth = imageWidth * baseScale;
        const scaledImageHeight = imageHeight * baseScale;
        const offsetX = (containerWidth - scaledImageWidth) / 2;
        const offsetY = (containerHeight - scaledImageHeight) / 2;

        // Apply transformations
        ctx.translate(offsetX + this.panX, offsetY + this.panY);
        ctx.scale(baseScale * this.zoomLevel, baseScale * this.zoomLevel);

        // Function to draw the image and bounding boxes
        const drawImageAndBoxes = (img) => {
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.translate(offsetX + this.panX, offsetY + this.panY);
            ctx.scale(baseScale * this.zoomLevel, baseScale * this.zoomLevel);
            ctx.drawImage(img, 0, 0);
            this.drawBoundingBoxes(ctx, data);
        };

        if (data.image_path) {
            // Check if we have a cached and fully loaded image for this path
            if (this.cachedImage && this.cachedImage.src === data.image_path && this.cachedImage.complete) {
                // Use cached image directly for instant rendering (no async loading)
                drawImageAndBoxes(this.cachedImage);
            } else {
                const img = new Image();
                img.crossOrigin = 'anonymous';
                img.onload = () => {
                    // Cache the loaded image
                    this.cachedImage = img;
                    drawImageAndBoxes(img);
                };
                img.onerror = () => {
                    ctx.setTransform(1, 0, 0, 1, 0, 0);
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    this.drawPlaceholderImage(ctx, scaledImageWidth / baseScale, scaledImageHeight / baseScale);
                    this.drawBoundingBoxes(ctx, data);
                };
                img.src = data.image_path;
            }
        } else {
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.drawPlaceholderImage(ctx, scaledImageWidth / baseScale, scaledImageHeight / baseScale);
            this.drawBoundingBoxes(ctx, data);
        }
    }


    drawBoundingBoxes(ctx, data) {
        const gtBoxes = data.ground_truth_boxes || [];
        const predBoxes = data.prediction_boxes || [];
        const fnBoxes = gtBoxes.filter(box => box.classification === 'fn');
        const fpBoxes = predBoxes.filter(box => box.classification === 'fp');
        const tpBoxes = predBoxes.filter(box => box.classification === 'tp');

        // Calculate box style based on image resolution (using height)
        const imageHeight = data.dimensions?.height || 1080;
        const scale = imageHeight / 1000;
        const lineWidth = Math.max(Math.ceil(imageHeight / 500), 1);
        const fontSize = Math.max(Math.ceil(imageHeight / 80 * 1.5), 8);
        const indicatorSize = Math.max(Math.ceil(imageHeight / 40), 16);
        const iconLineWidth = Math.max(1, lineWidth);

        if (this.showGTBoxes) {
            fnBoxes.forEach(box => this.drawBoundingBox(ctx, box, 'fn', scale, lineWidth, fontSize, indicatorSize, iconLineWidth));
        }
        if (this.showPredBoxes) {
            fpBoxes.forEach(box => this.drawBoundingBox(ctx, box, 'fp', scale, lineWidth, fontSize, indicatorSize, iconLineWidth));
            tpBoxes.forEach(box => this.drawBoundingBox(ctx, box, 'tp', scale, lineWidth, fontSize, indicatorSize, iconLineWidth));
        }
    }


    drawBoundingBox(ctx, box, type, scale, lineWidth, fontSize, indicatorSize, iconLineWidth) {
        const bbox = box.bbox;
        if (!bbox || bbox.length !== 4) return;

        const [x1, y1, x2, y2] = bbox;
        const width = x2 - x1;
        const height = y2 - y1;

        // Set style based on type
        let color;
        switch (type) {
            case 'tp':
                color = '#22c55e'; // green
                break;
            case 'fp':
                color = '#ef4444'; // red
                break;
            case 'fn':
                color = '#eab308'; // orange-yellow
                break;
            default:
                return;
        }

        // Draw bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;

        if (type === 'fn') {
            ctx.setLineDash([5, 3]); // Dashed line for FN
        } else {
            ctx.setLineDash([]);
        }

        ctx.strokeRect(x1, y1, width, height);
        ctx.setLineDash([]); // Reset dash

        // Draw corner indicator above the bounding box
        // Indicator's bottom boundary aligns with box's top (y1)
        // Indicator's left boundary aligns with box's left (x1)
        const indicatorX = x1;
        const indicatorY = y1 - indicatorSize;
        const centerX = indicatorX + indicatorSize / 2;
        const centerY = indicatorY + indicatorSize / 2;

        ctx.fillStyle = color;
        ctx.fillRect(indicatorX, indicatorY, indicatorSize, indicatorSize);

        // Draw icon in the corner indicator using canvas paths instead of text
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'white';
        ctx.lineWidth = iconLineWidth;

        if (type === 'tp') {
            // Draw checkmark (✓)
            ctx.beginPath();
            ctx.moveTo(centerX - Math.round(indicatorSize / 6), centerY);
            ctx.lineTo(centerX, centerY + Math.round(indicatorSize / 6));
            ctx.lineTo(centerX + Math.round(indicatorSize / 4), centerY - Math.round(6 * scale));
            ctx.stroke();
        } else if (type === 'fp') {
            // Draw cross (✗)
            ctx.beginPath();
            ctx.moveTo(centerX - Math.round(indicatorSize / 6), centerY - Math.round(4 * scale));
            ctx.lineTo(centerX + Math.round(4 * scale), centerY + Math.round(4 * scale));
            ctx.moveTo(centerX + Math.round(indicatorSize / 6), centerY - Math.round(4 * scale));
            ctx.lineTo(centerX - Math.round(4 * scale), centerY + 4);
            ctx.stroke();
        } else if (type === 'fn') {
            // Draw dash (—)
            ctx.beginPath();
            ctx.moveTo(centerX - Math.round(indicatorSize / 4), centerY);
            ctx.lineTo(centerX + Math.round(indicatorSize / 4), centerY);
            ctx.stroke();
        }

        // Draw label to the right of indicator
        // Label's bottom boundary aligns with box's top (y1)
        // Label's left boundary aligns with indicator's right (x1 + indicatorSize)
        if (this.showLabels) {
            let labelText = '';
            if (box.class_name) {
                labelText = box.class_name;
            }
            if (box.confidence !== undefined && box.confidence !== null) {
                labelText += ` (${box.confidence.toFixed(2)})`;
            }

            if (labelText) {
                ctx.font = fontSize + 'px Inter, sans-serif';
                const textMetrics = ctx.measureText(labelText);
                const labelWidth = textMetrics.width + Math.round(indicatorSize / 4);
                const labelHeight = indicatorSize;

                // Label is positioned to the right of the indicator
                // Left boundary aligns with indicator's right (x1 + indicatorSize)
                // Bottom boundary aligns with box's top (y1)
                const labelX = x1 + indicatorSize;
                const labelY = y1 - labelHeight;

                // Draw label background (semi-transparent)
                ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                ctx.fillRect(labelX, labelY, labelWidth, labelHeight);

                // Draw label text
                ctx.fillStyle = 'white';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'bottom';
                ctx.fillText(labelText, labelX + Math.round(indicatorSize / 8), y1);
            }
        }
    }

    setupToggleButtons() {
        // GT Boxes toggle
        const gtToggle = document.getElementById('toggle-gt-boxes');
        if (gtToggle) {
            gtToggle.addEventListener('click', () => {
                this.showGTBoxes = !this.showGTBoxes;
                gtToggle.classList.toggle('active');
                gtToggle.setAttribute('aria-pressed', this.showGTBoxes);
                this.reRenderCurrentImage();
            });
        }

        // Prediction Boxes toggle
        const predToggle = document.getElementById('toggle-pred-boxes');
        if (predToggle) {
            predToggle.addEventListener('click', () => {
                this.showPredBoxes = !this.showPredBoxes;
                predToggle.classList.toggle('active');
                predToggle.setAttribute('aria-pressed', this.showPredBoxes);
                this.reRenderCurrentImage();
            });
        }

        // Labels toggle
        const labelsToggle = document.getElementById('toggle-labels');
        if (labelsToggle) {
            labelsToggle.addEventListener('click', () => {
                this.showLabels = !this.showLabels;
                labelsToggle.classList.toggle('active');
                labelsToggle.setAttribute('aria-pressed', this.showLabels);
                this.reRenderCurrentImage();
            });
        }
    }

    reRenderCurrentImage() {
        // Re-render the current image with updated visibility settings
        if (this.currentImageData) {
            this.renderImageWithBoundingBoxes(this.currentImageData);
        }
    }

    setupZoomControls() {
        // Zoom in button
        const zoomInBtn = document.getElementById('zoom-in');
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => {
                this.zoomLevel = Math.min(this.zoomLevel + 0.25, 5.0); // Max zoom 5x
                this.updateZoomLevelDisplay();
                this.updateCanvasCursor();
                this.reRenderCurrentImage();
            });
        }

        // Zoom out button
        const zoomOutBtn = document.getElementById('zoom-out');
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => {
                this.zoomLevel = Math.max(this.zoomLevel - 0.25, 0.25); // Min zoom 0.25x
                this.updateZoomLevelDisplay();
                this.updateCanvasCursor();
                this.reRenderCurrentImage();
            });
        }

        // Reset zoom button
        const zoomResetBtn = document.getElementById('zoom-reset');
        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => {
                this.zoomLevel = 1.0;
                this.panX = 0;
                this.panY = 0;
                this.updateZoomLevelDisplay();
                this.updateCanvasCursor();
                this.reRenderCurrentImage();
            });
        }
    }

    updateZoomLevelDisplay() {
        const zoomDisplay = document.getElementById('zoom-level-display');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.zoomLevel * 100)}%`;
        }
    }

    setupPanDrag() {
        const canvas = document.getElementById('image-canvas');
        const container = document.getElementById('canvas-container');
        if (!canvas || !container) return;

        // Reset pan on new image load
        this.panX = 0;
        this.panY = 0;

        // Update cursor style based on zoom level
        this.updateCanvasCursor();

        // Mouse enter - hide scrollbar
        container.addEventListener('mouseenter', () => {
            container.classList.add('hide-scrollbar');
        });

        // Mouse leave - show scrollbar
        container.addEventListener('mouseleave', () => {
            container.classList.remove('hide-scrollbar');
        });

        // Mouse down - start dragging
        canvas.addEventListener('mousedown', (e) => {
            if (this.zoomLevel === 1.0) return; // Only allow panning when zoomed

            this.isDragging = true;
            this.dragStartX = e.clientX;
            this.dragStartY = e.clientY;
        });

        // Mouse move - update pan position
        canvas.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;

            const dx = e.clientX - this.dragStartX;
            const dy = e.clientY - this.dragStartY;

            this.panX += dx;
            this.panY += dy;

            this.dragStartX = e.clientX;
            this.dragStartY = e.clientY;

            this.reRenderCurrentImage();
        });

        // Mouse up - stop dragging
        canvas.addEventListener('mouseup', () => {
            this.isDragging = false;
        });

        // Mouse leave - stop dragging
        canvas.addEventListener('mouseleave', () => {
            this.isDragging = false;
        });
    }

    updateCanvasCursor() {
        const canvas = document.getElementById('image-canvas');
        if (!canvas) return;

        if (this.zoomLevel === 1.0) {
            canvas.classList.remove('zoomed');
        } else {
            canvas.classList.add('zoomed');
        }
    }

    navigateImage(direction) {
        const items = document.querySelectorAll('.image-list-item');
        if (items.length === 0) return;

        let currentIndex = -1;
        items.forEach((item, index) => {
            if (item.classList.contains('active')) {
                currentIndex = index;
            }
        });

        if (currentIndex === -1) return;

        let newIndex = currentIndex + direction;
        if (newIndex < 0) newIndex = items.length - 1;
        if (newIndex >= items.length) newIndex = 0;

        const newImageId = parseInt(items[newIndex].getAttribute('data-image-id'));
        this.selectImage(newImageId);
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

        // Load dataset button (comparison view)
        const comparisonLoadDatasetBtn = document.getElementById('comparison-load-dataset');
        if (comparisonLoadDatasetBtn) {
            comparisonLoadDatasetBtn.addEventListener('click', () => this.showLoadDatasetModal());
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

        // Class search input (for metrics table)
        const classSearch = document.getElementById('class-search');
        if (classSearch) {
            classSearch.addEventListener('input', (e) => {
                this.filterMetricsTable(e.target.value);
            });
        }

        // Image list search input
        const imageSearch = document.getElementById('image-search');
        if (imageSearch) {
            imageSearch.addEventListener('input', (e) => {
                this.filters.search = e.target.value;
                // Apply client-side filtering for search
                this.applyClientSideFilters();
            });
        }

        // Class filter dropdown
        const classFilter = document.getElementById('class-filter');
        if (classFilter) {
            classFilter.addEventListener('change', (e) => {
                this.filters.classFilter = e.target.value;
                // Reload images with new class filter
                this.loadImagesList();
            });
        }

        // Status filter dropdown
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filters.statusFilter = e.target.value;
                // Reload images with new status filter
                this.loadImagesList();
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

        // Separate Total row from class rows
        const totalRow = rows.find(row => row.classList.contains('total-row'));
        const classRows = rows.filter(row => !row.classList.contains('total-row'));

        if (classRows.length === 0) return;

        // Get column index
        const headerIndex = this.getColumnIndex(column);
        if (headerIndex === -1) return;

        // Sort class rows (exclude Total row from sorting)
        classRows.sort((rowA, rowB) => {
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

        // Clear table and re-add total row first, followed by sorted class rows
        tableBody.innerHTML = '';
        if (totalRow) {
            tableBody.appendChild(totalRow);
        }
        classRows.forEach(row => {
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
        const modalElement = document.getElementById('loadDatasetModal');
        const modal = new bootstrap.Modal(modalElement);
        modal.show();

        // Handle confirm button
        const confirmBtn = document.getElementById('confirm-load-dataset');
        if (confirmBtn) {
            // Remove old event listener if exists
            const newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

            newConfirmBtn.addEventListener('click', () => {
                const pathInput = document.getElementById('dataset-path');
                const path = pathInput?.value?.trim();

                if (!path) {
                    this.showError('Please enter a dataset path');
                    return;
                }

                // Hide modal and load dataset
                modal.hide();
                this.loadDataset(path);
            });
        }
    }

    async loadDataset(path) {
        try {
            this.showLoading();

            // Small delay to ensure loading overlay is visible during testing
            await new Promise(resolve => setTimeout(resolve, 1000));

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
                this.statisticsLoaded = false; // Reset statistics loaded flag for new dataset
                window.location.hash = '#dashboard';
                await this.loadStatistics();
            } else {
                // Handle error response with user-friendly message
                const errors = data.errors || [];
                if (errors.length > 0) {
                    // Show the actual error messages from the backend
                    this.showError(errors);
                } else {
                    this.showError('Failed to load dataset: Unknown error');
                }
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
            // Mark statistics as loaded
            this.statisticsLoaded = true;
        } catch (error) {
            this.showError('Error loading statistics');
        }
    }

    updateDashboard(data) {
        // Update summary cards
        if (data.overall_metrics) {
            document.getElementById('summary-total-images').textContent = data.overall_metrics.total_images || '-';
            document.getElementById('summary-total-classes').textContent = data.overall_metrics.total_classes !== undefined ? data.overall_metrics.total_classes : (data.classes?.length || '-');
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

        // Generate class rows
        const classRows = classes.map(cls => `
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

        // Calculate totals
        const totalGT = classes.reduce((sum, cls) => sum + (cls.total_gt_count || 0), 0);
        const totalPred = classes.reduce((sum, cls) => sum + (cls.total_pred_count || 0), 0);
        const totalTP = classes.reduce((sum, cls) => sum + (cls.tp_count || 0), 0);
        const totalFP = classes.reduce((sum, cls) => sum + (cls.fp_count || 0), 0);
        const totalFN = classes.reduce((sum, cls) => sum + (cls.fn_count || 0), 0);

        // Calculate metrics from totals
        const recall = (totalTP + totalFN) > 0 ? totalTP / (totalTP + totalFN) : undefined;
        const precision = (totalTP + totalFP) > 0 ? totalTP / (totalTP + totalFP) : undefined;
        // For FPR: FP / (FP + TN). Since we don't have TN, use totalPred as FP + TP
        // FPR = FP / (FP + (totalPred - FP - TP)) if we had TN, but we'll use a simplified approach
        // Using overall FPR: FP / (FP + GT) where GT represents potential negatives
        const fpr = (totalFP + totalGT) > 0 ? totalFP / (totalFP + totalGT) : undefined;
        const f1 = (recall !== undefined && precision !== undefined && (recall + precision) > 0)
            ? 2 * (precision * recall) / (precision + recall)
            : undefined;

        // Generate total row
        const totalRow = `
            <tr class="table-secondary total-row">
                <td><strong>Total</strong></td>
                <td><strong>${totalGT}</strong></td>
                <td><strong>${totalPred}</strong></td>
                <td><strong>${totalTP}</strong></td>
                <td><strong>${totalFP}</strong></td>
                <td><strong>${totalFN}</strong></td>
                <td><strong>${recall !== undefined ? recall.toFixed(3) : '-'}</strong></td>
                <td><strong>${precision !== undefined ? precision.toFixed(3) : '-'}</strong></td>
                <td><strong>${fpr !== undefined ? fpr.toFixed(3) : '-'}</strong></td>
                <td><strong>${f1 !== undefined ? f1.toFixed(3) : '-'}</strong></td>
            </tr>
        `;

        tableBody.innerHTML = totalRow + classRows;
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
        const modalElement = document.getElementById('errorModal');
        const modal = new bootstrap.Modal(modalElement);

        // Set error message
        const messageElement = document.getElementById('error-message');
        const detailsElement = document.getElementById('error-details');
        const errorListElement = document.getElementById('error-list');

        if (messageElement) {
            // Handle different message formats
            if (typeof message === 'string') {
                messageElement.textContent = message;
                // Hide details for single message
                if (detailsElement) {
                    detailsElement.style.display = 'none';
                }
            } else if (Array.isArray(message) && message.length > 0) {
                // Show first error as main message
                messageElement.textContent = message[0];
                // Show details if there are multiple errors
                if (detailsElement && errorListElement && message.length > 1) {
                    errorListElement.innerHTML = message.slice(1).map(err =>
                        `<li><i class="fas fa-exclamation-circle text-warning me-2" aria-hidden="true"></i>${this.escapeHtml(err)}</li>`
                    ).join('');
                    detailsElement.style.display = 'block';
                } else if (detailsElement) {
                    detailsElement.style.display = 'none';
                }
            } else if (message && message.error) {
                // Handle API error response format
                messageElement.textContent = message.error;
                if (detailsElement) {
                    detailsElement.style.display = 'none';
                }
            }
        }

        modal.show();
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
            // Always show Total row
            if (row.classList.contains('total-row')) {
                row.style.display = '';
                return;
            }

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
