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

        // Box visibility toggles
        this.showGTBoxes = true;
        this.showPredBoxes = true;
        this.showLabels = true;
        this.currentImageData = null; // Store current image data for re-rendering

        // Zoom and pan state
        this.zoomLevel = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;

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

        // Load statistics if dataset is loaded
        if (this.datasetId) {
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

    async loadImagesList() {
        if (!this.datasetId) return;

        try {
            // Build URL with filter parameters (class and status filters are server-side)
            let url = `/api/images/${this.datasetId}?per_page=50`;

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
                this.applyClientSideFilters();
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
            return;
        }

        container.innerHTML = images.map(image => {
            const statusClass = image.is_perfect ? 'status-perfect' : (image.has_fp || image.has_fn ? 'status-warning' : 'status-perfect');
            return `
                <div class="image-list-item" data-image-id="${image.id}">
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

        // Add click event listeners to image list items
        container.querySelectorAll('.image-list-item').forEach(item => {
            item.addEventListener('click', () => {
                const imageId = parseInt(item.getAttribute('data-image-id'));
                this.selectImage(imageId);
            });
        });
    }

    updateImagesList(images) {
        // Store images and apply client-side filters
        this.allImages = images;
        this.applyClientSideFilters();
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
                <div class="image-list-item" data-image-id="${image.id}">
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

        // Add click event listeners to image list items
        container.querySelectorAll('.image-list-item').forEach(item => {
            item.addEventListener('click', () => {
                const imageId = parseInt(item.getAttribute('data-image-id'));
                this.selectImage(imageId);
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

    async loadImageDetail(imageId) {
        if (!this.datasetId) return;

        const detailContent = document.getElementById('image-detail-content');
        if (detailContent) {
            detailContent.innerHTML = '<div class="text-center py-5"><i class="fas fa-spinner fa-spin fa-2x mb-3"></i><p>Loading image details...</p></div>';
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
                        <h5 class="mb-1"><i class="fas fa-image me-2"></i>${this.escapeHtml(data.filename)}</h5>
                        <p class="mb-0 text-muted">
                            <small>${data.dimensions ? `${data.dimensions.width} x ${data.dimensions.height} pixels` : ''}</small>
                        </p>
                    </div>
                    <div class="d-flex gap-2">
                        <button class="btn btn-outline-primary btn-sm" id="prev-image-btn">
                            <i class="fas fa-chevron-left me-1"></i> Previous
                        </button>
                        <button class="btn btn-outline-primary btn-sm" id="next-image-btn">
                            Next <i class="fas fa-chevron-right ms-1"></i>
                        </button>
                    </div>
                </div>
                <div class="d-flex gap-3">
                    <span class="badge bg-primary">GT: ${totalGT}</span>
                    <span class="badge bg-info">Pred: ${totalPred}</span>
                </div>

                <!-- Box Visibility Toggles -->
                <div class="d-flex gap-2 mb-3 mt-3">
                    <button class="btn btn-sm toggle-btn active" id="toggle-gt-boxes" title="Show/Hide Ground Truth Boxes">
                        <i class="fas fa-check-square me-1"></i> GT Boxes
                    </button>
                    <button class="btn btn-sm toggle-btn active" id="toggle-pred-boxes" title="Show/Hide Prediction Boxes">
                        <i class="fas fa-crosshairs me-1"></i> Pred Boxes
                    </button>
                    <button class="btn btn-sm toggle-btn active" id="toggle-labels" title="Show/Hide Labels">
                        <i class="fas fa-tag me-1"></i> Labels
                    </button>
                </div>

                <!-- Zoom Controls -->
                <div class="d-flex gap-2 mb-3">
                    <button class="btn btn-sm zoom-btn" id="zoom-out" title="Zoom Out">
                        <i class="fas fa-search-minus"></i>
                    </button>
                    <button class="btn btn-sm zoom-btn" id="zoom-reset" title="Reset Zoom">
                        <span id="zoom-level-display">100%</span>
                    </button>
                    <button class="btn btn-sm zoom-btn" id="zoom-in" title="Zoom In">
                        <i class="fas fa-search-plus"></i>
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
                        <h6 class="mb-0"><i class="fas fa-chart-bar me-2"></i>Per-Image Statistics</h6>
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

        // Render image with bounding boxes
        this.renderImageWithBoundingBoxes(data);

        // Add event listeners for toggle buttons
        this.setupToggleButtons();

        // Add event listeners for zoom controls
        this.setupZoomControls();

        // Add event listeners for pan/drag functionality
        this.setupPanDrag();
    }

    renderImageWithBoundingBoxes(data) {
        const canvas = document.getElementById('image-canvas');
        const ctx = canvas.getContext('2d');
        if (!canvas || !ctx) return;

        // Set canvas dimensions
        const width = data.dimensions?.width || 800;
        const height = data.dimensions?.height || 600;
        canvas.width = width;
        canvas.height = height;

        // Clear canvas and apply zoom/pan transforms
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Apply zoom and pan transformations
        ctx.translate(this.panX, this.panY);
        ctx.scale(this.zoomLevel, this.zoomLevel);

        // Create a placeholder image (since we don't have actual image files)
        // In a real implementation, you would load the actual image file
        this.drawPlaceholderImage(ctx, width, height);

        // Draw bounding boxes
        const gtBoxes = data.ground_truth_boxes || [];
        const predBoxes = data.prediction_boxes || [];

        // Combine all boxes for rendering
        // FN boxes are GT boxes without matching prediction (classification is null)
        const fnBoxes = gtBoxes.filter(box => box.classification === null);
        // FP boxes are prediction boxes without matching GT
        const fpBoxes = predBoxes.filter(box => box.classification === 'fp');
        // TP boxes are matched predictions (classification is 'tp')
        const tpBoxes = predBoxes.filter(box => box.classification === 'tp');

        // Draw GT boxes (FN only, since TP are predictions that match GT)
        if (this.showGTBoxes) {
            fnBoxes.forEach(box => this.drawBoundingBox(ctx, box, 'fn'));
        }

        // Draw prediction boxes (FP and TP)
        if (this.showPredBoxes) {
            fpBoxes.forEach(box => this.drawBoundingBox(ctx, box, 'fp'));
            tpBoxes.forEach(box => this.drawBoundingBox(ctx, box, 'tp'));
        }
    }

    drawPlaceholderImage(ctx, width, height) {
        // Draw a gradient background
        const gradient = ctx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, '#f0f9ff');
        gradient.addColorStop(1, '#e0f2fe');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);

        // Draw some placeholder shapes to simulate an image
        ctx.strokeStyle = '#cbd5e1';
        ctx.lineWidth = 1;

        // Draw a grid
        for (let x = 0; x < width; x += 50) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        for (let y = 0; y < height; y += 50) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Draw placeholder text
        ctx.fillStyle = '#94a3b8';
        ctx.font = '24px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Image Placeholder', width / 2, height / 2);
        ctx.font = '14px Inter, sans-serif';
        ctx.fillText(`${width} x ${height}`, width / 2, height / 2 + 30);
    }

    drawBoundingBox(ctx, box, type) {
        const bbox = box.bbox;
        if (!bbox || bbox.length !== 4) return;

        const [x1, y1, x2, y2] = bbox;
        const width = x2 - x1;
        const height = y2 - y1;

        // Set style based on type
        let color, lineWidth;
        switch (type) {
            case 'tp':
                color = '#22c55e'; // green
                lineWidth = 2;
                break;
            case 'fp':
                color = '#ef4444'; // red
                lineWidth = 2;
                break;
            case 'fn':
                color = '#ef4444'; // red
                lineWidth = 2;
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

        // Draw corner indicator (24x24px square at top-left)
        const indicatorSize = 24;
        const indicatorX = x1 - 2;
        const indicatorY = y1 - 12;
        const centerX = indicatorX + indicatorSize / 2;
        const centerY = indicatorY + indicatorSize / 2;

        ctx.fillStyle = color;
        ctx.fillRect(indicatorX, indicatorY, indicatorSize, indicatorSize);

        // Draw icon in the corner indicator using canvas paths instead of text
        ctx.fillStyle = 'white';
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;

        if (type === 'tp') {
            // Draw checkmark (✓)
            ctx.beginPath();
            ctx.moveTo(centerX - 4, centerY);
            ctx.lineTo(centerX, centerY + 4);
            ctx.lineTo(centerX + 6, centerY - 6);
            ctx.stroke();
        } else if (type === 'fp') {
            // Draw cross (✗)
            ctx.beginPath();
            ctx.moveTo(centerX - 4, centerY - 4);
            ctx.lineTo(centerX + 4, centerY + 4);
            ctx.moveTo(centerX + 4, centerY - 4);
            ctx.lineTo(centerX - 4, centerY + 4);
            ctx.stroke();
        } else if (type === 'fn') {
            // Draw dash (—)
            ctx.beginPath();
            ctx.moveTo(centerX - 6, centerY);
            ctx.lineTo(centerX + 6, centerY);
            ctx.stroke();
        }

        // Draw label (class name and confidence for predictions)
        if (this.showLabels) {
            let labelText = '';
            if (box.class_name) {
                labelText = box.class_name;
            }
            if (box.confidence !== undefined && box.confidence !== null) {
                labelText += ` (${box.confidence.toFixed(2)})`;
            }

            if (labelText) {
                ctx.font = '11px Inter, sans-serif';
                const textMetrics = ctx.measureText(labelText);
                const labelWidth = textMetrics.width + 12;
                const labelHeight = 20;

                // Draw label background (semi-transparent)
                ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                ctx.fillRect(x1, y1 + 12, labelWidth, labelHeight);

                // Draw label text
                ctx.fillStyle = 'white';
                ctx.textAlign = 'left';
                ctx.textBaseline = 'middle';
                ctx.fillText(labelText, x1 + 6, y1 + 22);
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
                this.reRenderCurrentImage();
            });
        }

        // Prediction Boxes toggle
        const predToggle = document.getElementById('toggle-pred-boxes');
        if (predToggle) {
            predToggle.addEventListener('click', () => {
                this.showPredBoxes = !this.showPredBoxes;
                predToggle.classList.toggle('active');
                this.reRenderCurrentImage();
            });
        }

        // Labels toggle
        const labelsToggle = document.getElementById('toggle-labels');
        if (labelsToggle) {
            labelsToggle.addEventListener('click', () => {
                this.showLabels = !this.showLabels;
                labelsToggle.classList.toggle('active');
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
                        `<li><i class="fas fa-exclamation-circle text-warning me-2"></i>${this.escapeHtml(err)}</li>`
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
