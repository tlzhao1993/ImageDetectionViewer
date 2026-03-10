from flask import Flask, jsonify, request, Response, send_file
from flask_cors import CORS
import os
import sys
import csv
import io
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

@app.route('/api/dataset/current')
def get_current_dataset_endpoint():
    """
    API endpoint to get the most recently loaded dataset

    Returns:
        JSON response with:
            - dataset_id (int): ID of most recent dataset, or null if no dataset loaded
            - dataset_path (str): Path to most recent dataset
    """
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Get the most recent dataset
            cursor.execute('''
                SELECT id, path
                FROM dataset_metadata
                ORDER BY id DESC
                LIMIT 1
            ''')

            row = cursor.fetchone()

            if row is None:
                return jsonify({
                    'dataset_id': None,
                    'dataset_path': None
                }), 200

            return jsonify({
                'dataset_id': row[0],
                'dataset_path': row[1]
            }), 200

    except Exception as e:
        return jsonify({
            'dataset_id': None,
            'dataset_path': None,
            'error': str(e)
        }), 500


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
                'total_images': dataset_row[2],  # Total images in dataset
                'total_classes': dataset_row[3],  # Total classes in dataset
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


@app.route('/api/statistics/export/<int:dataset_id>')
def export_statistics_endpoint(dataset_id):
    """
    API endpoint to export statistics in CSV or JSON format

    Args:
        dataset_id: ID of dataset to export statistics for

    Query parameters:
        format: Export format - 'csv' or 'json' (default: 'json')

    Returns:
        CSV format:
            - Content-Type: text/csv
            - CSV file with columns: Class, GT Count, Pred Count, TP, FP, FN, Recall, Precision, FPR, F1 Score
        JSON format:
            - Content-Type: application/json
            - JSON with classes array and overall_metrics
    """
    try:
        # Get format parameter (default to json)
        export_format = request.args.get('format', 'json').lower()

        # Validate format
        if export_format not in ['csv', 'json']:
            return jsonify({
                'success': False,
                'error': 'format must be either "csv" or "json"'
            }), 400

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

            # Return based on format
            if export_format == 'csv':
                # Create CSV content
                output = io.StringIO()
                writer = csv.writer(output)

                # Write header row
                writer.writerow([
                    'Class', 'GT Count', 'Pred Count', 'TP', 'FP', 'FN',
                    'Recall', 'Precision', 'FPR', 'F1 Score'
                ])

                # Write data rows
                for cls in classes:
                    writer.writerow([
                        cls['name'],
                        cls['total_gt_count'],
                        cls['total_pred_count'],
                        cls['tp_count'],
                        cls['fp_count'],
                        cls['fn_count'],
                        f"{cls['recall']:.6f}",
                        f"{cls['precision']:.6f}",
                        f"{cls['fpr']:.6f}",
                        f"{cls['f1_score']:.6f}"
                    ])

                # Write overall metrics row
                writer.writerow([
                    'OVERALL',
                    overall_metrics['total_gt_boxes'],
                    overall_metrics['total_pred_boxes'],
                    overall_metrics['total_tp'],
                    overall_metrics['total_fp'],
                    overall_metrics['total_fn'],
                    f"{overall_metrics['recall']:.6f}",
                    f"{overall_metrics['precision']:.6f}",
                    f"{overall_metrics['fpr']:.6f}",
                    f"{overall_metrics['f1_score']:.6f}"
                ])

                csv_content = output.getvalue()
                output.close()

                # Return CSV response
                response = Response(
                    csv_content,
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename=statistics_dataset_{dataset_id}.csv'
                    }
                )
                return response

            else:  # json format
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
                # Convert thumbnail_path from 'app/static/thumbnails/file.png' to '/static/thumbnails/file.png'
                thumbnail_path = row[4]
                if thumbnail_path and thumbnail_path.startswith('app/static/'):
                    thumbnail_path = thumbnail_path.replace('app/static/', '/static/')
                images.append({
                    'id': row[0],
                    'filename': row[1],
                    'width': row[2],
                    'height': row[3],
                    'thumbnail_path': thumbnail_path,
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


@app.route('/api/images/<int:dataset_id>/<int:image_id>')
def get_image_detail_endpoint(dataset_id, image_id):
    """
    API endpoint to get detailed data for a single image

    Args:
        dataset_id: ID of dataset
        image_id: ID of image to retrieve details for

    Returns:
        JSON response with:
            - success (bool): Whether request was successful
            - filename (str): Image filename
            - dimensions (dict): Image width and height
            - ground_truth_boxes (list): Array of ground truth bounding boxes
            - prediction_boxes (list): Array of prediction bounding boxes
            - per_class_stats (dict): Statistics breakdown by class
            - thumbnail_path (str): Path to thumbnail

    Each box in ground_truth_boxes and prediction_boxes contains:
        - id (int): Box ID
        - class_name (str): Class name
        - bbox (list): [x1, y1, x2, y2] coordinates
        - confidence (float): Confidence score (predictions only)
        - iou (float): IoU value (for matched boxes only)
        - classification (str): 'tp', 'fp', 'fn', or null

    Each entry in per_class_stats contains:
        - gt_count (int): Number of ground truth boxes
        - pred_count (int): Number of prediction boxes
        - tp (int): True positives
        - fp (int): False positives
        - fn (int): False negatives
    """
    try:
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

            # Get image metadata
            cursor.execute('''
                SELECT id, filename, width, height, thumbnail_path, image_path,
                       total_gt_boxes, total_pred_boxes
                FROM image_metadata
                WHERE id = ? AND dataset_id = ?
            ''', (image_id, dataset_id))

            image_row = cursor.fetchone()

            if image_row is None:
                return jsonify({
                    'success': False,
                    'error': f'Image with ID {image_id} not found in dataset {dataset_id}'
                }), 404

            # Get all bounding boxes for this image
            cursor.execute('''
                SELECT bb.id, bb.class_id, bb.type, bb.x1, bb.y1, bb.x2, bb.y2,
                       bb.confidence, bb.iou, bb.classification, c.name
                FROM bounding_boxes bb
                JOIN classes c ON bb.class_id = c.id
                WHERE bb.image_id = ?
                ORDER BY bb.id
            ''', (image_id,))

            bbox_rows = cursor.fetchall()

            # Separate ground truth and prediction boxes
            ground_truth_boxes = []
            prediction_boxes = []

            for row in bbox_rows:
                (bbox_id, class_id, bbox_type, x1, y1, x2, y2,
                 confidence, iou, classification, class_name) = row

                box_data = {
                    'id': bbox_id,
                    'class_name': class_name,
                    'bbox': [x1, y1, x2, y2],
                    'iou': iou,
                    'classification': classification
                }

                if bbox_type == 'ground_truth':
                    ground_truth_boxes.append(box_data)
                elif bbox_type == 'prediction':
                    box_data['confidence'] = confidence
                    prediction_boxes.append(box_data)

            # Calculate per-class statistics for this image
            cursor.execute('''
                SELECT c.name, bb.type, bb.classification
                FROM bounding_boxes bb
                JOIN classes c ON bb.class_id = c.id
                WHERE bb.image_id = ?
            ''', (image_id,))

            class_rows = cursor.fetchall()

            per_class_stats = {}

            for class_name, bbox_type, classification in class_rows:
                if class_name not in per_class_stats:
                    per_class_stats[class_name] = {
                        'gt_count': 0,
                        'pred_count': 0,
                        'tp': 0,
                        'fp': 0,
                        'fn': 0
                    }

                stats = per_class_stats[class_name]

                if bbox_type == 'ground_truth':
                    stats['gt_count'] += 1
                    if classification == 'fn':
                        stats['fn'] += 1
                    elif classification == 'tp':
                        stats['tp'] += 1
                elif bbox_type == 'prediction':
                    stats['pred_count'] += 1
                    if classification == 'fp':
                        stats['fp'] += 1

            # Convert thumbnail_path from 'app/static/thumbnails/file.png' to '/static/thumbnails/file.png'
            thumbnail_path = image_row[4]
            if thumbnail_path and thumbnail_path.startswith('app/static/'):
                thumbnail_path = thumbnail_path.replace('app/static/', '/static/')

            # Get actual image dimensions from the image file itself
            # This ensures dimensions match the actual image, not potentially incorrect GT/pred file dimensions
            image_path = image_row[5]
            actual_width = image_row[2]
            actual_height = image_row[3]

            try:
                from PIL import Image
                with Image.open(image_path) as img:
                    actual_width, actual_height = img.size
            except Exception as e:
                # If reading image dimensions fails, fall back to database values
                pass

            return jsonify({
                'success': True,
                'filename': image_row[1],
                'dimensions': {
                    'width': actual_width,
                    'height': actual_height
                },
                'ground_truth_boxes': ground_truth_boxes,
                'prediction_boxes': prediction_boxes,
                'per_class_stats': per_class_stats,
                'thumbnail_path': thumbnail_path,
                'image_path': f'/api/images/{dataset_id}/{image_id}/file'
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/images/<int:dataset_id>/<int:image_id>/file')
def get_image_file_endpoint(dataset_id, image_id):
    """
    API endpoint to serve the actual image file

    Args:
        dataset_id: ID of the dataset
        image_id: ID of the image to retrieve

    Returns:
        The image file
    """
    try:
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

            # Get image metadata with image_path
            cursor.execute('''
                SELECT image_path
                FROM image_metadata
                WHERE id = ? AND dataset_id = ?
            ''', (image_id, dataset_id))

            image_row = cursor.fetchone()

            if image_row is None:
                return jsonify({
                    'success': False,
                    'error': f'Image with ID {image_id} not found in dataset {dataset_id}'
                }), 404

            image_path = image_row[0]

            if not image_path or not os.path.exists(image_path):
                return jsonify({
                    'success': False,
                    'error': f'Image file not found at {image_path}'
                }), 404

            # Serve the image file
            return send_file(image_path)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Serve the main HTML page"""
    return app.jinja_env.get_or_select_template('base.html').render()

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
