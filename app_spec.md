```xml
<project_specification>
  <project_name>Image Detection Result Analyzer - Frontend Tool</project_name>

  <overview>
    Build a comprehensive frontend tool with a Flask backend to analyze the performance of object detection models by comparing ground truth annotations with model predictions. The application will process local datasets consisting of image sequences, ground truth bounding box JSON files, and model prediction JSON files (containing bounding boxes, classes, and confidence scores). It provides two core views: a statistics dashboard displaying per-class detection metrics (recall, false positive rate, etc.) and an image-by-image comparison view showing visual overlays of ground truth and predicted bounding boxes with distinct visual indicators for correct detections, false positives, and missed detections. The tool prioritizes intuitive visualization, accurate metric calculation, and seamless local file handling.
  </overview>

  <technology_stack>
    <frontend>
      <framework>Vanilla HTML5, CSS3, JavaScript (ES6+)</framework>
      <styling>Custom CSS with Flexbox/Grid, optional Bootstrap 5 (via CDN) for responsive layout</styling>
      <visualization>Chart.js (CDN) for statistical charts, Canvas API for bounding box rendering</visualization>
      <file_handling>FileReader API for local file processing</file_handling>
      <routing>Client-side routing with JavaScript (hash-based) for page navigation</routing>
      <icons>Font Awesome (CDN) for visual indicators (check, cross, dash)</icons>
    </frontend>
    <backend>
      <runtime>Python 3.8+</runtime>
      <framework>Flask 2.0+</framework>
      <data_processing>
        - JSON parsing with built-in json module
        - Image processing with Pillow (PIL) for thumbnail generation
        - Metric calculation (recall, precision, FPR) with numpy
      </data_processing>
      <cors>Flask-CORS for cross-origin resource sharing</cors>
      <file_management>Built-in os/pathlib for local file system interaction</file_management>
    </backend>
    <communication>
      <api>RESTful endpoints for data processing and retrieval</api>
      <data_format>JSON for all data exchange between frontend and backend</data_format>
      <file_upload>Multipart/form-data for batch file upload (optional) or local file path specification</file_handling>
    </communication>
    <dependencies>
      <python>
        - flask>=2.0.0
        - flask-cors>=3.0.10
        - pillow>=9.0.0
        - numpy>=1.21.0
      </python>
      <frontend_cdn>
        - Chart.js v4.4.0
        - Bootstrap 5.3.0 (optional)
        - Font Awesome 6.4.0
      </frontend_cdn>
    </dependencies>
  </technology_stack>

  <prerequisites>
    <environment_setup>
      - Python 3.8+ installed on the system
      - Flask and required dependencies installed via pip: pip install flask flask-cors pillow numpy
      - Local dataset organized in a structured directory (images in /images, ground truth JSON in /gt, predictions JSON in /predictions)
      - Backend code in /app directory with app.py as entry point
      - Frontend assets (HTML/CSS/JS) in /app/static directory
      - Template files in /app/templates directory
      - Environment variables (optional) for dataset path configuration (.env file with DATASET_PATH)
    </environment_setup>
    <dataset_format>
      <image_sequence>
        - All images in a single directory (JPG/PNG format) with consistent naming convention (e.g., img_001.jpg, img_002.png)
        - Image dimensions consistent or variable (tool should handle both)
      </image_sequence>
      <ground_truth_json>
        - Single JSON file or per-image JSON files (naming matching images: img_001.json)
        - Structure: {
            "filename": "img_001.jpg",
            "width": 1920,
            "height": 1080,
            "annotations": [
              {
                "class": "car",
                "bbox": [x1, y1, x2, y2]  # pixel coordinates (top-left, bottom-right)
              },
              ...
            ]
          }
      </ground_truth_json>
      <prediction_json>
        - Single JSON file or per-image JSON files (naming matching images: img_001_pred.json)
        - Structure: {
            "filename": "img_001.jpg",
            "width": 1920,
            "height": 1080,
            "predictions": [
              {
                "class": "car",
                "bbox": [x1, y1, x2, y2],
                "score": 0.95  # confidence score (0-1)
              },
              ...
            ]
          }
      </prediction_json>
    </dataset_format>
  </prerequisites>

  <core_features>
    <file_handling>
      - Local dataset path configuration (input field for directory path)
      - Validation of dataset structure (check for images, GT JSON, prediction JSON)
      - Batch parsing of all files in the dataset directory
      - Error handling for missing files, invalid JSON formats, and mismatched filenames
      - Thumbnail generation for all images (150x150px, aspect ratio preserved)
      - Caching of parsed data to avoid reprocessing on page refresh
    </file_handling>

    <statistics_dashboard>
      <metrics_calculation>
        - **Recall (True Positive Rate)**: TP / (TP + FN) per class
        - **Precision**: TP / (TP + FP) per class
        - **False Positive Rate (FPR)**: FP / (FP + TN) per class
        - **F1 Score**: 2 * (Precision * Recall) / (Precision + Recall) per class
        - **Overall Accuracy**: (TP + TN) / (TP + TN + FP + FN)
        - **Average Precision (AP)** per class (optional)
        - **Intersection over Union (IoU)** threshold configuration (default: 0.5) for TP/FP/FN classification
      </metrics_calculation>
      <visualization>
        - Bar charts for per-class recall, precision, FPR
        - Pie charts for class distribution in ground truth vs predictions
        - Summary table with all metrics for easy comparison
        - Sortable and filterable metric table (by class name, metric value)
        - Export statistics to CSV/JSON format
        - Interactive tooltips on charts showing exact metric values
      </visualization>
      <user_interface>
        - Dropdown for IoU threshold adjustment (0.3 to 0.9 in 0.1 increments)
        - Class filter (show/hide specific classes in charts/tables)
        - Confidence score threshold filter for predictions (0.0 to 1.0 slider)
        - Reset filters button to restore default settings
        - Summary card with key overall metrics (total images, total classes, average recall/precision)
      </user_interface>
    </statistics_dashboard>

    <image_comparison_view>
      <left_panel>
        - Searchable and filterable file list (by filename, class presence)
        - Image thumbnails alongside filenames (150x150px)
        - Scrollable list with fixed height (occupies 100% of viewport height)
        - Highlight active/selected image in the list
        - Pagination (optional) for large datasets (10/20/50 images per page)
        - Class filter (show only images containing specific classes)
        - Status filter (show only images with FP/FN/perfect detections)
      </left_panel>
      <right_panel>
        <image_display>
          - High-resolution image view (scaled to fit viewport, maintain aspect ratio)
          - Interactive canvas overlay for bounding boxes
          - Bounding box styles:
            - True Positive (TP): Green border (2px), green checkmark (✓) at top-left corner
            - False Positive (FP): Red border (2px), red cross (✗) at top-left corner
            - False Negative (FN): Red border (2px), red horizontal dash (—) at top-left corner
          - Bounding box labels (class name + confidence score for predictions)
          - Zoom/pan functionality for detailed inspection
          - Toggle visibility of ground truth/prediction boxes
          - Toggle visibility of box labels/indicators
        </image_display>
        <per_image_statistics>
          - Summary card for current image (filename, dimensions, total GT boxes, total predicted boxes)
          - Per-class breakdown table (GT count, predicted count, TP, FP, FN for each class)
          - IoU values for each matched bounding box (optional tooltip on hover)
          - Confidence score distribution for predictions on current image
          - Navigation buttons (previous/next image) for sequential viewing
        </per_image_statistics>
      </right_panel>
    </image_comparison_view>

    <navigation>
      - Top navigation bar with links to Statistics Dashboard and Image Comparison View
      - Active page indicator in navigation bar
      - Breadcrumb navigation for context (current dataset path, current image)
      - Back to top button for long pages (statistics dashboard)
      - Responsive navigation (collapsible menu on mobile devices)
    </navigation>

    <error_handling>
      - User-friendly error messages for invalid dataset paths
      - Validation errors for malformed JSON files (line number + error description)
      - Warning messages for mismatched filenames (GT/prediction JSON without corresponding image)
      - Loading spinners during data processing/file parsing
      - Empty state handling (no data loaded, no images to display)
      - Fallback UI for unsupported image formats
    </error_handling>

    <accessibility>
      - Keyboard navigation (Tab/Enter for list selection, arrow keys for image navigation)
      - Alt text for all images and icons
      - High contrast mode for bounding boxes (optional toggle)
      - Screen reader compatible labels for all UI elements
      - Responsive design for mobile/tablet/desktop viewing
      - Text size adjustment option (small/medium/large)
    </accessibility>
  </core_features>

  <database_schema>
    <tables>
      <dataset_metadata>
        - id (primary key, integer)
        - path (text, unique)
        - total_images (integer)
        - total_classes (integer)
        - iou_threshold (float, default 0.5)
        - confidence_threshold (float, default 0.5)
        - created_at (timestamp)
        - last_updated (timestamp)
      </dataset_metadata>

      <image_metadata>
        - id (primary key, integer)
        - dataset_id (foreign key to dataset_metadata.id)
        - filename (text)
        - width (integer)
        - height (integer)
        - thumbnail_path (text)
        - total_gt_boxes (integer)
        - total_pred_boxes (integer)
        - has_fp (boolean)
        - has_fn (boolean)
        - is_perfect (boolean)
      </image_metadata>

      <classes>
        - id (primary key, integer)
        - dataset_id (foreign key to dataset_metadata.id)
        - name (text, unique per dataset)
        - total_gt_count (integer)
        - total_pred_count (integer)
        - tp_count (integer)
        - fp_count (integer)
        - fn_count (integer)
        - recall (float)
        - precision (float)
        - fpr (float)
        - f1_score (float)
      </classes>

      <bounding_boxes>
        - id (primary key, integer)
        - image_id (foreign key to image_metadata.id)
        - class_id (foreign key to classes.id)
        - type (text, enum: 'ground_truth', 'prediction')
        - x1 (float)
        - y1 (float)
        - x2 (float)
        - y2 (float)
        - confidence (float, null for ground truth)
        - iou (float, null for unmatched boxes)
        - classification (text, enum: 'tp', 'fp', 'fn', null for unclassified)
      </bounding_boxes>
    </tables>
    <notes>
      - Database is SQLite (file-based) for simplicity, stored as dataset_analysis.db
      - Data is cleared/overwritten when a new dataset is loaded
      - Indexes on filename, class name, and image_id for faster queries
    </notes>
  </database_schema>

  <api_endpoints_summary>
    <dataset>
      - POST /api/dataset/load: Load and parse dataset from provided path
        - Request body: { "dataset_path": "/path/to/dataset", "iou_threshold": 0.5 }
        - Response: { "success": true, "dataset_id": 1, "total_images": 100, "total_classes": 5, "errors": [] }
      - GET /api/dataset/metadata/:id: Get dataset metadata and summary statistics
      - DELETE /api/dataset/:id: Clear dataset from memory/database
    </dataset>

    <statistics>
      - GET /api/statistics/:dataset_id: Get all per-class statistics
        - Response: { "classes": [...], "overall_metrics": {...}, "iou_threshold": 0.5 }
      - POST /api/statistics/recalculate: Recalculate metrics with new thresholds
        - Request body: { "dataset_id": 1, "iou_threshold": 0.6, "confidence_threshold": 0.7 }
        - Response: { "success": true, "statistics": {...} }
      - GET /api/statistics/export/:dataset_id: Export statistics to CSV/JSON
        - Query params: { "format": "csv" }
    </statistics>

    <images>
      - GET /api/images/:dataset_id: Get list of all images with metadata (filename, thumbnail path, basic stats)
        - Query params: { "page": 1, "per_page": 20, "class_filter": "car", "status_filter": "fp" }
      - GET /api/images/:dataset_id/:image_id: Get detailed data for single image
        - Response: { 
            "filename": "img_001.jpg", 
            "dimensions": { "width": 1920, "height": 1080 },
            "ground_truth_boxes": [...],
            "prediction_boxes": [...],
            "per_class_stats": {...},
            "thumbnail_path": "/static/thumbnails/img_001.jpg"
          }
      - GET /api/images/thumbnail/:dataset_id/:filename: Serve generated thumbnail image
    </images>

    <classes>
      - GET /api/classes/:dataset_id: Get list of all classes in dataset with counts
      - GET /api/classes/:dataset_id/:class_id: Get detailed statistics for single class
    </classes>

    <health>
      - GET /api/health: Check server status and version
        - Response: { "status": "healthy", "version": "1.0.0", "python_version": "3.9.7", "flask_version": "2.2.3" }
    </health>
  </api_endpoints_summary>

  <ui_layout>
    <main_structure>
      - Fixed top navigation bar (100% width, 60px height) with project title and page links
      - Main content area (fills remaining viewport height) with:
        - Statistics Dashboard: Single column layout with summary cards, charts, and tables
        - Image Comparison View: Two-column layout (25% left panel, 75% right panel)
      - Responsive breakpoints:
        - Mobile (<768px): Image Comparison View switches to single column (list at top, image view below)
        - Tablet (768px-1024px): Left panel 30%, right panel 70%
        - Desktop (>1024px): Left panel 25%, right panel 75%
      - Footer (optional) with version info and basic help link (fixed at bottom)
    </main_structure>

    <statistics_dashboard_layout>
      - Header section with:
        - Page title ("Detection Statistics Dashboard")
        - Control panel (IoU slider, confidence slider, class filter dropdown)
        - Export button (CSV/JSON)
      - Summary cards section (3-4 cards in row):
        - Total Images Processed
        - Number of Classes
        - Average Recall (all classes)
        - Average Precision (all classes)
      - Charts section (2 charts per row):
        - Per-Class Recall (bar chart)
        - Per-Class Precision (bar chart)
        - Per-Class FPR (bar chart)
        - Class Distribution (ground truth vs predictions) (pie/donut chart)
      - Detailed metrics table section:
        - Sortable table with columns: Class, GT Count, Pred Count, TP, FP, FN, Recall, Precision, FPR, F1 Score
        - Pagination for tables with >20 classes
        - Search box for filtering table rows
    </statistics_dashboard_layout>

    <image_comparison_layout>
      <left_panel_layout>
        - Search bar (top of panel, 100% width)
        - Filter section (class filter dropdown, status filter radio buttons)
        - Image list container (scrollable, 100% remaining height):
          - Each list item: Thumbnail (left) + Filename (right) + status indicator (small color dot: green=perfect, yellow=FP/FN, red=many errors)
          - Hover state: Highlight background
          - Active state: Bold text + colored border
      </left_panel_layout>
      <right_panel_layout>
        - Image header section:
          - Filename and navigation buttons (previous/next)
          - Toggle buttons (show/hide GT boxes, show/hide prediction boxes, show/hide labels)
          - Zoom controls (+/-/reset)
        - Image display container (max height: 70% of viewport):
          - Centered image with canvas overlay for bounding boxes
          - Scrollbars if image exceeds container size
        - Per-image statistics section:
          - Summary card (filename, dimensions, total boxes)
          - Per-class breakdown table (Class, GT, Pred, TP, FP, FN)
          - Confidence score histogram (optional)
      </right_panel_layout>
    </image_comparison_layout>

    <modals_overlays>
      - Dataset Load Modal: Input field for dataset path, load button, validation messages
      - Error Modal: Displays detailed error information with close button
      - Help Modal: Basic instructions for using the tool (keyboard shortcuts, IoU explanation)
      - Export Modal: Options for export format (CSV/JSON) and data scope (all classes/specific classes)
      - Loading Overlay: Semi-transparent overlay with spinner during data processing
    </modals_overlays>
  </ui_layout>

  <design_system>
    <color_palette>
      - Primary: #2c5282 (deep blue) - navigation, buttons, headers
      - Success (TP): #22c55e (green) - border, checkmark icon
      - Error (FP/FN): #ef4444 (red) - border, cross/dash icons
      - Neutral: 
        - Background: #f8fafc (light mode), #1e293b (dark mode)
        - Text: #1e293b (light mode), #f8fafc (dark mode)
        - Border: #e2e8f0 (light mode), #334155 (dark mode)
        - Highlight: #f0f9ff (light mode), #0f172a (dark mode)
      - Chart colors: Distinct hues for each class (using categorical color scale)
    </color_palette>

    <typography>
      - Font family: Inter, system-ui, sans-serif (fallback)
      - Font sizes:
        - Heading 1 (page title): 2rem (32px), font-bold
        - Heading 2 (section title): 1.5rem (24px), font-semibold
        - Heading 3 (card title): 1.25rem (20px), font-medium
        - Body text: 1rem (16px), font-normal
        - Small text (labels, captions): 0.875rem (14px), font-normal
      - Line height:
        - Headings: 1.2
        - Body: 1.5
      - Text alignment:
        - Headings: Left-aligned
        - Body: Left-aligned
        - Table data: Center-aligned (numeric values), left-aligned (text)
    </typography>

    <components>
      <buttons>
        - Primary button: Solid primary color background, white text, rounded corners (8px), padding (8px 16px)
        - Secondary button: Transparent background, primary color border, primary color text, rounded corners (8px)
        - Icon button: Square (32px), transparent background, icon centered, hover state (light background)
        - Disabled state: 50% opacity, no pointer events, cursor: not-allowed
      </buttons>

      <tables>
        - Bordered table with alternating row background (zebra striping)
        - Header row: Primary color background, white text
        - Hover state: Light highlight background
        - Sortable columns: Arrow indicator on active sort column
      </tables>

      <bounding_boxes>
        - Border width: 2px
        - Corner indicators: 24x24px square at top-left corner with icon (check/cross/dash)
        - Label style: Small semi-transparent background (black/white), white/black text, padding (2px 4px), rounded corners (4px)
        - IoU visualization (optional): Gradient border based on IoU value (green=high, yellow=medium, red=low)
      </bounding_boxes>

      <cards>
        - Rounded corners (8px)
        - Subtle shadow (box-shadow: 0 1px 3px rgba(0,0,0,0.12))
        - Padding (16px)
        - Border (1px solid neutral border color)
        - Header section (optional): Slightly darker background, padding (8px 16px)
      </cards>

      <inputs>
        - Text input: Rounded corners (8px), border (1px solid neutral border), padding (8px 12px), focus state (primary color border, subtle shadow)
        - Slider: Custom styled range input with primary color track
        - Dropdown: Styled select element matching input style, with custom arrow icon
      </inputs>
    </components>

    <animations>
      - Transition duration: 200ms (all interactive elements)
      - Hover animations: Subtle scale (1.02x) for buttons/cards, color change for links
      - Page transitions: Fade in/out (opacity 0 to 1)
      - Loading spinner: Rotating circle with gradient border
      - Bounding box highlight: Pulse animation on hover (optional)
      - Table sorting: Fade animation for row reordering
      - Image loading: Skeleton placeholder until image is fully loaded
    </animations>
  </design_system>

  <key_interactions>
    <dataset_loading_flow>
      1. User clicks "Load Dataset" button, opening dataset path modal
      2. User enters local dataset path (or selects directory via file picker, optional)
      3. User clicks "Load" button, triggering loading overlay
      4. Backend validates dataset structure and parses all files
      5. Backend calculates initial metrics (IoU=0.5, confidence=0.5)
      6. Frontend redirects to Statistics Dashboard with loaded data
      7. If errors occur, error modal displays with list of issues (missing files, invalid JSON)
    </dataset_loading_flow>

    <statistics_interaction_flow>
      1. User views summary cards with key metrics
      2. User adjusts IoU/confidence sliders to recalculate metrics (real-time update)
      3. User filters classes via dropdown (charts/tables update automatically)
      4. User hovers over chart bars to see exact metric values (tooltips)
      5. User clicks table headers to sort by specific metric
      6. User clicks "Export" button to download statistics in CSV/JSON format
      7. User clicks "View Images" link to navigate to Image Comparison View
    </statistics_interaction_flow>

    <image_comparison_interaction_flow>
      1. User navigates to Image Comparison View (retains current filters from statistics page)
      2. User searches/filters image list (left panel) to find specific images
      3. User clicks image thumbnail/filename in left panel:
         a. Right panel loads selected image
         b. Canvas overlay renders all bounding boxes with appropriate indicators
         c. Per-image statistics update to show current image's metrics
      4. User uses toggle buttons to show/hide GT/prediction boxes
      5. User uses zoom controls to inspect specific regions of the image
      6. User hovers over bounding boxes to see detailed info (IoU, confidence score)
      7. User uses previous/next buttons to navigate sequentially through images
    </key_interactions>

  <implementation_steps>
    <step number="1">
      <title>Project Setup and Environment Configuration</title>
      <tasks>
        - Initialize Flask project structure (app.py, static/, templates/, requirements.txt)
        - Set up virtual environment and install dependencies (Flask, Flask-CORS, Pillow, numpy)
        - Configure Flask app with CORS support and static file serving
        - Create basic HTML templates (base.html with navigation, statistics.html, image_view.html)
        - Implement environment variable handling for dataset path
        - Create health check endpoint (/api/health)
      </tasks>
    </step>

    <step number="2">
      <title>Backend File Parsing and Data Processing</title>
      <tasks>
        - Implement dataset validation function (check for required files/directories)
        - Create JSON parsing functions for ground truth and prediction files
        - Implement thumbnail generation using Pillow
        - Create SQLite database schema and connection logic
        - Implement metric calculation functions (recall, precision, FPR, F1)
        - Create IoU calculation function for bounding box matching
        - Implement API endpoint for dataset loading (/api/dataset/load)
      </tasks>
    </step>

    <step number="3">
      <title>Backend API Development</title>
      <tasks>
        - Implement API endpoints for statistics retrieval (/api/statistics/:dataset_id)
        - Create endpoint for metric recalculation with custom thresholds
        - Implement image list and detail endpoints (/api/images/*)
        - Create class list and detail endpoints (/api/classes/*)
        - Implement export functionality (CSV/JSON) for statistics
        - Add error handling and validation for all API endpoints
        - Add logging for debugging (file parsing errors, metric calculations)
      </tasks>
    </step>

    <step number="4">
      <title>Frontend Statistics Dashboard Implementation</title>
      <tasks>
        - Create HTML structure for statistics page (summary cards, charts, tables)
        - Implement Chart.js integration for bar/pie charts
        - Add interactive sliders for IoU/confidence threshold adjustment
        - Implement AJAX calls to retrieve and update statistics data
        - Create sortable/filterable metrics table with JavaScript
        - Add export functionality (button to trigger API export endpoint)
        - Implement responsive design for all screen sizes
      </tasks>
    </step>

    <step number="5">
      <title>Frontend Image Comparison View Implementation</title>
      <tasks>
        - Create two-column layout for image list and detail view
        - Implement image list with thumbnails, search, and filters
        - Create image display canvas for bounding box rendering
        - Implement bounding box drawing logic (different styles for TP/FP/FN)
        - Add zoom/pan functionality for image inspection
        - Implement per-image statistics table
        - Add navigation buttons (previous/next) for sequential viewing
        - Adapt layout for mobile devices (single column)
      </tasks>
    </step>

    <step number="6">
      <title>UI Polish and Design System Implementation</title>
      <tasks>
        - Apply color palette and typography across all pages
        - Implement component styles (buttons, tables, cards, inputs)
        - Add animations and transitions for interactive elements
        - Create loading overlays and empty state designs
        - Implement error modals and user feedback messages
        - Add accessibility features (alt text, keyboard navigation)
        - Ensure consistent styling across all UI elements
      </tasks>
    </step>

    <step number="7">
      <title>Testing and Error Handling</title>
      <tasks>
        - Test with sample dataset (images + GT/prediction JSON files)
        - Validate all metric calculations (manual verification)
        - Test edge cases (empty dataset, no FP/FN, single class)
        - Implement comprehensive error handling for invalid inputs
        - Test responsive design on different screen sizes
        - Verify accessibility compliance (keyboard navigation, screen reader support)
        - Optimize performance for large datasets (lazy loading, pagination)
      </tasks>
    </step>

    <step number="8">
      <title>Final Optimization and Documentation</title>
      <tasks>
        - Optimize image loading (lazy loading for thumbnails)
        - Cache parsed data to avoid reprocessing
        - Add inline help/tooltips for complex features (IoU, FPR)
        - Create user documentation (README with setup/usage instructions)
        - Add code comments and clean up code structure
        - Test end-to-end workflow (load dataset → view stats → inspect images)
        - Final UI polish and bug fixes
      </tasks>
    </step>
  </implementation_steps>

  <success_criteria>
    <functionality>
      - Dataset loading works reliably with valid local dataset paths
      - All metrics (recall, precision, FPR, F1) calculate accurately (verified against manual calculations)
      - Statistics dashboard updates in real-time with threshold adjustments
      - Image comparison view correctly renders all bounding boxes with proper visual indicators
      - Bounding box classification (TP/FP/FN) is accurate based on IoU threshold
      - All filters (class, status, confidence) work correctly across both views
      - Export functionality generates valid CSV/JSON files with complete statistics
      - Error handling provides clear, actionable feedback for common issues
    </functionality>

    <user_experience>
      - Interface is intuitive and requires minimal learning curve
      - All interactions are responsive (no lag >200ms for datasets <1000 images)
      - Visual indicators for TP/FP/FN are clear and distinguishable
      - Navigation between views is seamless (retains filter settings)
      - Image zoom/pan functionality works smoothly for detailed inspection
      - Responsive design works well on mobile, tablet, and desktop
      - Loading states provide clear feedback during data processing
    </user_experience>

    <technical_quality>
      - Clean, maintainable code structure (separation of concerns: backend/frontend)
      - Proper error handling for file I/O, JSON parsing, and API requests
      - Efficient data processing (parses 1000 images in <30 seconds on standard hardware)
      - SQLite database queries are optimized with proper indexing
      - Frontend uses efficient DOM manipulation (minimal re-renders)
      - Code is well-documented with comments and follows best practices
      - No memory leaks (tested with repeated dataset loading/unloading)
    </technical_quality>

    <design_polish>
      - Consistent design language across all UI elements
      - Clear visual hierarchy (important metrics stand out)
      - Professional, uncluttered interface with appropriate whitespace
      - High contrast for bounding boxes (easily visible on all image types)
      - Smooth animations that enhance (not distract from) the user experience
      - Accessible color palette (complies with WCAG contrast standards)
      - Intuitive iconography (check/cross/dash) with clear meaning
    </design_polish>
  </success_criteria>
</project_specification>
```