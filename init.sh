#!/bin/bash

# Image Detection Result Analyzer - Workspace Initialization Script
# This script sets up the development environment and project structure

set -e  # Exit on error

echo "=========================================="
echo "Image Detection Result Analyzer"
echo "Workspace Initialization"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored message
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_step() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Step 1: Check Python version
print_step "Step 1: Checking Python version"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_success "Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python version meets requirements (>= 3.8)"

# Step 2: Create virtual environment
print_step "Step 2: Creating virtual environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# Step 3: Upgrade pip
print_step "Step 3: Upgrading pip"
pip install --upgrade pip > /dev/null 2>&1
print_success "pip upgraded"

# Step 4: Install Python dependencies
print_step "Step 4: Installing Python dependencies"

echo "Installing packages from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed from requirements.txt"
else
    print_warning "requirements.txt not found. Installing dependencies manually..."
    pip install flask>=2.0.0 flask-cors>=3.0.10 pillow>=9.0.0 numpy>=1.21.0
    print_success "Core dependencies installed"
fi

# Step 5: Create project directory structure
print_step "Step 5: Creating project directory structure"

# Create app directory if it doesn't exist
if [ ! -d "app" ]; then
    mkdir -p app
    print_success "Created app directory"
else
    print_success "app directory already exists"
fi

# Create static subdirectories
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/thumbnails
print_success "Created static directory structure"

# Create templates directory
mkdir -p app/templates
print_success "Created templates directory"

# Create data directory for database and cache
mkdir -p app/data
print_success "Created data directory"

# Step 6: Create requirements.txt if it doesn't exist
print_step "Step 6: Setting up requirements.txt"

if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << EOF
flask>=2.0.0
flask-cors>=3.0.10
pillow>=9.0.0
numpy>=1.21.0
EOF
    print_success "Created requirements.txt"
else
    print_success "requirements.txt already exists"
fi

# Step 7: Create basic Flask app structure
print_step "Step 7: Setting up Flask application structure"

if [ ! -f "app.py" ]; then
    cat > app.py << 'EOF'
from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Configuration
app.config['DATASET_PATH'] = os.environ.get('DATASET_PATH', './dataset')
app.config['DATABASE_PATH'] = os.path.join('app', 'data', 'dataset_analysis.db')
app.config['THUMBNAIL_SIZE'] = (150, 150)

@app.route('/api/health')
def health_check():
    """Health check endpoint to verify server status"""
    import sys
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'flask_version': Flask.__version__
    })

@app.route('/')
def index():
    """Serve the main HTML page"""
    return "Image Detection Result Analyzer - Backend Running"

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    os.makedirs(os.path.join('app', 'static', 'thumbnails'), exist_ok=True)

    print("==========================================")
    print("Image Detection Result Analyzer")
    print("Flask Server Starting...")
    print("==========================================")
    print(f"Python Version: {app.config['python_version']}")
    print(f"Flask Version: {Flask.__version__}")
    print(f"Dataset Path: {app.config['DATASET_PATH']}")
    print(f"Database Path: {app.config['DATABASE_PATH']}")
    print("==========================================")

    app.run(debug=True, host='0.0.0.0', port=5000)
EOF
    print_success "Created app.py with basic Flask structure"
else
    print_success "app.py already exists"
fi

# Step 8: Create basic HTML template
print_step "Step 8: Creating HTML templates"

if [ ! -f "app/templates/base.html" ]; then
    cat > app/templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Detection Result Analyzer</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Custom CSS -->
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#dashboard">
                <i class="fas fa-chart-line me-2"></i>
                Detection Result Analyzer
            </a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="#dashboard" id="nav-dashboard">
                            <i class="fas fa-chart-bar me-1"></i> Statistics Dashboard
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="#comparison" id="nav-comparison">
                            <i class="fas fa-images me-1"></i> Image Comparison
                        </a>
                    </li>
                    <li class="nav-item">
                        <button class="btn btn-light btn-sm ms-2" id="btn-load-dataset">
                            <i class="fas fa-folder-open me-1"></i> Load Dataset
                        </button>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main id="main-content">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-light text-center py-3 mt-5">
        <div class="container">
            <small class="text-muted">
                Image Detection Result Analyzer v1.0.0 |
                <a href="#" data-bs-toggle="modal" data-bs-target="#helpModal">Help</a>
            </small>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom JS -->
    <script src="/static/js/app.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
EOF
    print_success "Created base.html template"
else
    print_success "base.html already exists"
fi

# Step 9: Create basic CSS file
print_step "Step 9: Creating CSS styles"

if [ ! -f "app/static/css/style.css" ]; then
    cat > app/static/css/style.css << 'EOF'
/* Image Detection Result Analyzer - Main Stylesheet */

:root {
    --primary-color: #2c5282;
    --success-color: #22c55e;
    --error-color: #ef4444;
    --warning-color: #eab308;
    --bg-light: #f8fafc;
    --bg-dark: #1e293b;
    --text-light: #1e293b;
    --text-dark: #f8fafc;
    --border-light: #e2e8f0;
    --border-dark: #334155;
}

body {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background-color: var(--bg-light);
    color: var(--text-light);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Navigation */
.navbar {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-link.active {
    font-weight: 600;
}

/* Cards */
.card {
    border: 1px solid var(--border-light);
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
    transform: translateY(2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.15);
}

.card-header {
    background-color: rgba(44, 82, 130, 0.05);
    border-bottom: 1px solid var(--border-light);
}

/* Buttons */
.btn-primary {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-primary:hover {
    background-color: #1a365d;
    border-color: #1a365d;
}

/* Summary Cards */
.summary-card {
    text-align: center;
}

.summary-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary-color);
}

.summary-card .metric-label {
    color: #64748b;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Image Comparison View */
.image-view-container {
    height: 100vh;
    padding-top: 56px; /* Offset for navbar */
}

.image-list-panel {
    height: calc(100vh - 56px);
    overflow-y: auto;
    border-right: 1px solid var(--border-light);
}

.image-list-item {
    padding: 12px;
    border-bottom: 1px solid var(--border-light);
    cursor: pointer;
    transition: background-color 0.2s;
}

.image-list-item:hover {
    background-color: var(--bg-light);
}

.image-list-item.active {
    background-color: #f0f9ff;
    border-left: 4px solid var(--primary-color);
    font-weight: 600;
}

.image-list-item .thumbnail {
    width: 60px;
    height: 60px;
    object-fit: cover;
    border-radius: 4px;
}

.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
}

.status-perfect { background-color: var(--success-color); }
.status-warning { background-color: var(--warning-color); }
.status-error { background-color: var(--error-color); }

.image-detail-panel {
    height: calc(100vh - 56px);
    overflow-y: auto;
}

/* Canvas Overlay */
.canvas-container {
    position: relative;
    display: inline-block;
    background-color: #1a1a1a;
}

#image-canvas {
    display: block;
}

/* Tables */
.table {
    margin-bottom: 0;
}

.table thead {
    background-color: var(--primary-color);
    color: white;
}

.table tbody tr:nth-child(even) {
    background-color: #f8fafc;
}

.table tbody tr:hover {
    background-color: #f0f9ff;
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.spinner {
    width: 60px;
    height: 60px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
    text-align: center;
    padding: 60px 20px;
}

.empty-state i {
    font-size: 64px;
    color: #cbd5e1;
    margin-bottom: 20px;
}

.empty-state h3 {
    color: #64748b;
    margin-bottom: 10px;
}

.empty-state p {
    color: #94a3b8;
    margin-bottom: 20px;
}

/* Sliders */
.form-range::-webkit-slider-thumb {
    background-color: var(--primary-color);
}

.form-range::-moz-range-thumb {
    background-color: var(--primary-color);
}

/* Responsive */
@media (max-width: 768px) {
    .image-view-container {
        flex-direction: column;
    }

    .image-list-panel,
    .image-detail-panel {
        height: auto;
        border-right: none;
    }
}
EOF
    print_success "Created style.css"
else
    print_success "style.css already exists"
fi

# Step 10: Create basic JavaScript file
print_step "Step 10: Creating JavaScript application"

if [ ! -f "app/static/js/app.js" ]; then
    cat > app/static/js/app.js << 'EOF'
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
EOF
    print_success "Created app.js"
else
    print_success "app.js already exists"
fi

# Step 11: Print summary and useful information
print_step "Initialization Complete - Summary"

echo ""
print_success "Project structure created successfully!"
echo ""
echo "Directory Structure:"
tree -L 3 -I 'venv|__pycache__|*.pyc' 2>/dev/null || find . -maxdepth 3 -type d -not -path '*/venv/*' -not -path '*/\.*' | head -20
echo ""
echo "=========================================="
echo "Useful Commands:"
echo "=========================================="
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start Flask server:"
echo "   python app.py"
echo ""
echo "3. Access the application:"
echo "   http://localhost:5000"
echo ""
echo "4. Check health endpoint:"
echo "   curl http://localhost:5000/api/health"
echo ""
echo "5. Install additional packages:"
echo "   pip install <package_name>"
echo ""
echo "=========================================="
echo "Environment Information:"
echo "=========================================="
echo ""
echo "Python: $PYTHON_VERSION"
echo "Flask: $(flask --version 2>/dev/null | cut -d' ' -f2 || echo 'not installed')"
echo "Working Directory: $(pwd)"
echo "Virtual Environment: venv/"
echo ""
echo "Configuration:"
echo "  - Dataset Path: ./dataset (set via DATASET_PATH env var)"
echo "  - Database: app/data/dataset_analysis.db"
echo "  - Thumbnails: app/static/thumbnails/"
echo "  - Port: 5000"
echo ""
print_success "Workspace initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Create a sample dataset in ./dataset directory"
echo "3. Run: python app.py"
echo "4. Open http://localhost:5000 in your browser"
echo ""
