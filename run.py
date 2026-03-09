from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import flask
from app.db import init_db, get_db
from app.loader import load_dataset, recalculate_statistics

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


@app.route('/api/statistics/recalculate', methods=['POST'])
def recalculate_statistics_endpoint():
    """
    API endpoint to recalculate statistics with new thresholds

    Request body:
        dataset_id (int): ID of the dataset to recalculate
        iou_threshold (float, optional): New IoU threshold (default: keep current)
        confidence_threshold (float, optional): New confidence threshold (default: keep current)

    Returns:
        JSON response with:
            - success (bool): Whether recalculation was successful
            - classes (list): Array of class statistics with updated metrics
            - overall_metrics (dict): Overall metrics across all classes
            - iou_threshold (float): Updated IoU threshold
            - confidence_threshold (float): Updated confidence threshold
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

        dataset_id = data.get('dataset_id')
        new_iou_threshold = data.get('iou_threshold')
        new_confidence_threshold = data.get('confidence_threshold')

        # Validate required parameters
        if dataset_id is None:
            return jsonify({
                'success': False,
                'error': 'dataset_id is required'
            }), 400

        try:
            dataset_id = int(dataset_id)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'dataset_id must be a valid integer'
            }), 400

        # Validate thresholds if provided
        if new_iou_threshold is not None:
            try:
                new_iou_threshold = float(new_iou_threshold)
                if not (0.0 <= new_iou_threshold <= 1.0):
                    return jsonify({
                        'success': False,
                        'error': 'iou_threshold must be between 0.0 and 1.0'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'iou_threshold must be a valid number'
                }), 400

        if new_confidence_threshold is not None:
            try:
                new_confidence_threshold = float(new_confidence_threshold)
                if not (0.0 <= new_confidence_threshold <= 1.0):
                    return jsonify({
                        'success': False,
                        'error': 'confidence_threshold must be between 0.0 and 1.0'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'confidence_threshold must be a valid number'
                }), 400

        # If thresholds not provided, get current thresholds from database
        if new_iou_threshold is None or new_confidence_threshold is None:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT iou_threshold, confidence_threshold
                    FROM dataset_metadata
                    WHERE id = ?
                ''', (dataset_id,))

                dataset_row = cursor.fetchone()

                if dataset_row is None:
                    return jsonify({
                        'success': False,
                        'error': f'Dataset with ID {dataset_id} not found'
                    }), 404

                if new_iou_threshold is None:
                    new_iou_threshold = dataset_row[0]
                if new_confidence_threshold is None:
                    new_confidence_threshold = dataset_row[1]

        # Recalculate statistics
        result = recalculate_statistics(
            dataset_id=dataset_id,
            iou_threshold=new_iou_threshold,
            confidence_threshold=new_confidence_threshold
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


@app.route('/api/images/<int:dataset_id>')
def get_images_endpoint(dataset_id):
    """
    API endpoint to get paginated list of images for a dataset

    Args:
        dataset_id: ID of the dataset to retrieve images for
        page (int, optional): Page number (default: 1)
        per_page (int, optional): Number of images per page (default: 20)
        class_filter (str, optional): Filter by class name
        status_filter (str, optional): Filter by status (fp, fn, perfect)

    Query parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20, max: 100)
        class_filter: Only show images containing this class
        status_filter: Only show images with this status (fp, fn, perfect)

    Returns:
        JSON response with:
            - success (bool): Whether request was successful
            - images (list): Array of image entries
            - total (int): Total number of images
            - page (int): Current page number
            - per_page (int): Items per page
            - total_pages (int): Total number of pages

    Each image entry contains:
            - id (int): Image ID
            - filename (str): Image filename
            - width (int): Image width
            - height (int): Image height
            - thumbnail_path (str): Path to thumbnail
            - total_gt_boxes (int): Number of GT boxes
            - total_pred_boxes (int): Number of prediction boxes
            - has_fp (bool): Has false positives
            - has_fn (bool): Has false negatives
            - is_perfect (bool): Perfect detection (no FP or FN)
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        class_filter = request.args.get('class_filter')
        status_filter = request.args.get('status_filter')

        # Validate parameters
        if page < 1:
            return jsonify({
                'success': False,
                'error': 'page must be a positive integer'
            }), 400

        if per_page < 1 or per_page > 100:
            return jsonify({
                'success': False,
                'error': 'per_page must be between 1 and 100'
            }), 400

        # Validate status_filter
        valid_status_filters = ['fp', 'fn', 'perfect']
        if status_filter is not None and status_filter not in valid_status_filters:
            return jsonify({
                'success': False,
                'error': f'status_filter must be one of: {", ".join(valid_status_filters)}'
            }), 400

        with get_db() as conn:
            cursor = conn.cursor()

            # Check if dataset exists
            cursor.execute('''
                SELECT id FROM dataset_metadata WHERE id = ?
            ''', (dataset_id,))

            if cursor.fetchone() is None:
                return jsonify({
                    'success': False,
                    'error': f'Dataset with ID {dataset_id} not found'
                }), 404

            # Build base query with filters
            base_query = '''
                SELECT id, filename, width, height, thumbnail_path,
                       total_gt_boxes, total_pred_boxes, has_fp, has_fn, is_perfect
                FROM image_metadata
                WHERE dataset_id = ?
            '''
            query_params = [dataset_id]

            # Add class filter if provided
            if class_filter:
                base_query += '''
                    AND id IN (
                        SELECT im.id FROM image_metadata im
                        JOIN bounding_boxes bb ON bb.image_id = im.id
                        JOIN classes c ON bb.class_id = c.id
                        WHERE im.dataset_id = ? AND c.name = ? AND bb.type = 'ground_truth'
                    )
                '''
                query_params.append(dataset_id)
                query_params.append(class_filter)

            # Add status filter if provided
            if status_filter == 'fp':
                base_query += ' AND has_fp = 1'
            elif status_filter == 'fn':
                base_query += ' AND has_fn = 1'
            elif status_filter == 'perfect':
                base_query += ' AND is_perfect = 1'

            # Add ordering and pagination
            base_query += ' ORDER BY id'
            base_query += ' LIMIT ? OFFSET ?'
            offset = (page - 1) * per_page
            query_params.extend([per_page, offset])

            # Execute query to get images
            cursor.execute(base_query, query_params)

            # Fetch images before executing count query
            images = []
            for row in cursor.fetchall():
                images.append({
                    'id': row[0],
                    'filename': row[1],
                    'width': row[2],
                    'height': row[3],
                    'thumbnail_path': row[4],
                    'total_gt_boxes': row[5],
                    'total_pred_boxes': row[6],
                    'has_fp': bool(row[7]),
                    'has_fn': bool(row[8]),
                    'is_perfect': bool(row[9])
                })

            # Get total count
            count_query = '''
                SELECT COUNT(*) FROM image_metadata WHERE dataset_id = ?
            '''
            count_params = [dataset_id]

            if class_filter:
                count_query += '''
                    AND id IN (
                        SELECT im.id FROM image_metadata im
                        JOIN bounding_boxes bb ON bb.image_id = im.id
                        JOIN classes c ON bb.class_id = c.id
                        WHERE im.dataset_id = ? AND c.name = ? AND bb.type = 'ground_truth'
                    )
                '''
                count_params.append(dataset_id)
                count_params.append(class_filter)

            if status_filter == 'fp':
                count_query += ' AND has_fp = 1'
            elif status_filter == 'fn':
                count_query += ' AND has_fn = 1'
            elif status_filter == 'perfect':
                count_query += ' AND is_perfect = 1'

            cursor.execute(count_query, count_params)
            total_count = cursor.fetchone()[0]

            # Calculate total pages
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

            return jsonify({
                'success': True,
                'images': images,
                'total': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages
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
