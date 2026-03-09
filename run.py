from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import flask
from app.db import init_db
from app.loader import load_dataset

app = Flask(__name__, static_folder='app/static', template_folder='app/templates')
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
        'flask_version': flask.__version__
    })

@app.route('/api/dataset/load', methods=['POST'])
def load_dataset_endpoint():
    """
    API endpoint to load and parse a dataset

    Request body:
        dataset_path (str): Path to dataset directory
        iou_threshold (float, optional): IoU threshold for TP/FP classification (default: 0.5)
        confidence_threshold (float, optional): Minimum confidence score (default: 0.5)

    Returns:
        JSON response with:
            - success (bool): Whether loading was successful
            - dataset_id (int): ID of loaded dataset
            - total_images (int): Number of images processed
            - total_classes (int): Number of unique classes
            - errors (list): List of any errors encountered
    """
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        dataset_path = data.get('dataset_path')
        iou_threshold = data.get('iou_threshold', 0.5)
        confidence_threshold = data.get('confidence_threshold', 0.5)

        # Validate required parameters
        if not dataset_path:
            return jsonify({
                'success': False,
                'error': 'dataset_path is required'
            }), 400

        # Validate thresholds
        try:
            iou_threshold = float(iou_threshold)
            if not (0.0 <= iou_threshold <= 1.0):
                return jsonify({
                    'success': False,
                    'error': 'iou_threshold must be between 0.0 and 1.0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'iou_threshold must be a valid number'
            }), 400

        try:
            confidence_threshold = float(confidence_threshold)
            if not (0.0 <= confidence_threshold <= 1.0):
                return jsonify({
                    'success': False,
                    'error': 'confidence_threshold must be between 0.0 and 1.0'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'confidence_threshold must be a valid number'
            }), 400

        # Load the dataset
        result = load_dataset(
            dataset_path=dataset_path,
            iou_threshold=iou_threshold,
            confidence_threshold=confidence_threshold
        )

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Serve the main HTML page"""
    return "Image Detection Result Analyzer - Backend Running"

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    os.makedirs(os.path.join('app', 'static', 'thumbnails'), exist_ok=True)

    # Initialize database with schema
    init_db()

    print("==========================================")
    print("Image Detection Result Analyzer")
    print("Flask Server Starting...")
    print("==========================================")
    print(f"Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Flask Version: {flask.__version__}")
    print(f"Dataset Path: {app.config['DATASET_PATH']}")
    print(f"Database Path: {app.config['DATABASE_PATH']}")
    print("==========================================")

    app.run(debug=True, host='0.0.0.0', port=5000)
