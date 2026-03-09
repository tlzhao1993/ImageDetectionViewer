from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import flask
from app.db import init_db, get_db
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


@app.route('/api/statistics/<int:dataset_id>')
def get_statistics_endpoint(dataset_id):
    """
    API endpoint to retrieve per-class statistics for a dataset

    Args:
        dataset_id: ID of the dataset to retrieve statistics for

    Returns:
        JSON response with:
            - classes (list): Array of class statistics with metrics
            - overall_metrics (dict): Overall metrics across all classes
            - iou_threshold (float): IoU threshold used
            - confidence_threshold (float): Confidence threshold used

    Each class in classes array contains:
        - id (int): Class ID
        - name (str): Class name
        - total_gt_count (int): Number of ground truth boxes
        - total_pred_count (int): Number of prediction boxes
        - tp_count (int): Number of true positives
        - fp_count (int): Number of false positives
        - fn_count (int): Number of false negatives
        - recall (float): Recall metric
        - precision (float): Precision metric
        - fpr (float): False positive rate
        - f1_score (float): F1 Score
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Check if dataset exists
            cursor.execute('''
                SELECT id, path, total_images, total_classes, iou_threshold, confidence_threshold
                FROM dataset_metadata
                WHERE id = ?
            ''', (dataset_id,))

            dataset_row = cursor.fetchone()

            if dataset_row is None:
                return jsonify({
                    'success': False,
                    'error': f'Dataset with ID {dataset_id} not found'
                }), 404

            # Get all classes for this dataset
            cursor.execute('''
                SELECT id, name, total_gt_count, total_pred_count,
                       tp_count, fp_count, fn_count,
                       recall, precision, fpr, f1_score
                FROM classes
                WHERE dataset_id = ?
                ORDER BY name
            ''', (dataset_id,))

            classes = []
            for row in cursor.fetchall():
                classes.append({
                    'id': row[0],
                    'name': row[1],
                    'total_gt_count': row[2],
                    'total_pred_count': row[3],
                    'tp_count': row[4],
                    'fp_count': row[5],
                    'fn_count': row[6],
                    'recall': row[7],
                    'precision': row[8],
                    'fpr': row[9],
                    'f1_score': row[10]
                })

            # Calculate overall metrics
            total_tp = sum(c['tp_count'] for c in classes)
            total_fp = sum(c['fp_count'] for c in classes)
            total_fn = sum(c['fn_count'] for c in classes)
            total_gt = sum(c['total_gt_count'] for c in classes)

            # Overall recall
            if (total_tp + total_fn) > 0:
                overall_recall = total_tp / (total_tp + total_fn)
            else:
                overall_recall = 0.0

            # Overall precision
            if (total_tp + total_fp) > 0:
                overall_precision = total_tp / (total_tp + total_fp)
            else:
                overall_precision = 0.0

            # Overall F1 Score
            if (overall_precision + overall_recall) > 0:
                overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall)
            else:
                overall_f1 = 0.0

            # Overall FPR
            if (total_fp + total_tp) > 0:
                overall_fpr = total_fp / (total_fp + total_tp)
            else:
                overall_fpr = 0.0

            overall_metrics = {
                'total_gt_boxes': total_gt,
                'total_pred_boxes': sum(c['total_pred_count'] for c in classes),
                'total_tp': total_tp,
                'total_fp': total_fp,
                'total_fn': total_fn,
                'recall': overall_recall,
                'precision': overall_precision,
                'fpr': overall_fpr,
                'f1_score': overall_f1
            }

            return jsonify({
                'success': True,
                'classes': classes,
                'overall_metrics': overall_metrics,
                'iou_threshold': dataset_row[4],
                'confidence_threshold': dataset_row[5]
            }), 200

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
