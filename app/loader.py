"""
Dataset loader module for Image Detection Result Analyzer
Handles loading and parsing datasets, processing images, annotations, and predictions
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

from app.validator import validate_dataset
from app.parser import parse_ground_truth_file, parse_prediction_file, get_unique_classes_from_gt, get_unique_classes_from_pred
from app.thumbnail import generate_thumbnail, get_thumbnail_path
from app.metrics import calculate_iou, classify_bounding_boxes, calculate_class_metrics
from app.db import get_db, DATABASE_PATH


def load_dataset(dataset_path: str, iou_threshold: float = 0.5, confidence_threshold: float = 0.5) -> Dict[str, Any]:
    """
    Load and parse a dataset for analysis

    Args:
        dataset_path: Path to dataset directory
        iou_threshold: IoU threshold for TP/FP classification (default: 0.5)
        confidence_threshold: Minimum confidence score for predictions (default: 0.5)

    Returns:
        Dictionary containing:
        - success (bool): Whether loading was successful
        - dataset_id (int): ID of the loaded dataset
        - total_images (int): Number of images processed
        - total_classes (int): Number of unique classes
        - errors (list): List of any errors encountered

    Raises:
        ValueError: If dataset validation fails
        FileNotFoundError: If required files are missing
    """
    # Validate dataset
    validation_result = validate_dataset(dataset_path)
    if not validation_result['valid']:
        return {
            'success': False,
            'errors': validation_result['errors'],
            'dataset_path': dataset_path
        }

    path = Path(dataset_path)
    images_dir = path / 'images'
    gt_dir = path / 'gt'
    predictions_dir = path / 'predictions'

    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}

    # Collect all image files
    image_files = [
        f for f in images_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    if len(image_files) == 0:
        return {
            'success': False,
            'errors': ['No image files found in images/ directory'],
            'dataset_path': dataset_path
        }

    # Create mapping from filename stem to image file
    image_map = {f.stem: f for f in image_files}

    # Collect all GT and prediction files
    gt_files = {f.stem.replace('_gt', '').replace('_pred', ''): f for f in gt_dir.iterdir() if f.is_file() and f.suffix.lower() == '.json'}
    pred_files = {f.stem.replace('_gt', '').replace('_pred', ''): f for f in predictions_dir.iterdir() if f.is_file() and f.suffix.lower() == '.json'}

    # Parse all data
    parsed_data = []
    errors = []

    for image_stem, image_file in image_map.items():
        try:
            # Get corresponding GT and prediction files
            gt_file = gt_files.get(image_stem)
            pred_file = pred_files.get(image_stem)

            if gt_file is None and pred_file is None:
                errors.append(f"No annotation files found for {image_file.name}")
                continue

            data_entry = {
                'image_path': str(image_file),
                'image_filename': image_file.name,
                'image_stem': image_stem,
                'gt_data': None,
                'pred_data': None
            }

            # Parse GT file if exists
            if gt_file is not None:
                try:
                    gt_data = parse_ground_truth_file(str(gt_file))
                    data_entry['gt_data'] = gt_data
                except Exception as e:
                    errors.append(f"Error parsing GT file {gt_file.name}: {e}")

            # Parse prediction file if exists
            if pred_file is not None:
                try:
                    pred_data = parse_prediction_file(str(pred_file))
                    data_entry['pred_data'] = pred_data
                except Exception as e:
                    errors.append(f"Error parsing prediction file {pred_file.name}: {e}")

            # Only include if we have at least one annotation file
            if data_entry['gt_data'] is not None or data_entry['pred_data'] is not None:
                parsed_data.append(data_entry)

        except Exception as e:
            errors.append(f"Error processing {image_file.name}: {e}")

    if len(parsed_data) == 0:
        return {
            'success': False,
            'errors': errors + ['No valid image-annotation pairs found'],
            'dataset_path': dataset_path
        }

    # Generate thumbnails and collect all classes
    all_classes = set()
    thumbnail_dir = os.path.join('app', 'static', 'thumbnails')
    os.makedirs(thumbnail_dir, exist_ok=True)

    for entry in parsed_data:
        # Generate thumbnail
        try:
            entry['thumbnail_path'] = generate_thumbnail(
                entry['image_path'],
                output_dir=thumbnail_dir,
                size=(150, 150),
                preserve_aspect_ratio=True
            )
        except Exception as e:
            errors.append(f"Error generating thumbnail for {entry['image_filename']}: {e}")
            entry['thumbnail_path'] = None

        # Collect classes from GT
        if entry['gt_data']:
            classes = get_unique_classes_from_gt(entry['gt_data'])
            all_classes.update(classes)

        # Collect classes from predictions
        if entry['pred_data']:
            classes = get_unique_classes_from_pred(entry['pred_data'])
            all_classes.update(classes)

    all_classes = sorted(list(all_classes))

    # Store data in database
    dataset_id = store_dataset_in_database(
        dataset_path=dataset_path,
        parsed_data=parsed_data,
        all_classes=all_classes,
        iou_threshold=iou_threshold,
        confidence_threshold=confidence_threshold,
        errors=errors
    )

    return {
        'success': True,
        'dataset_id': dataset_id,
        'total_images': len(parsed_data),
        'total_classes': len(all_classes),
        'errors': errors,
        'dataset_path': dataset_path
    }


def store_dataset_in_database(
    dataset_path: str,
    parsed_data: List[Dict[str, Any]],
    all_classes: List[str],
    iou_threshold: float,
    confidence_threshold: float,
    errors: List[str]
) -> int:
    """
    Store parsed dataset data in database

    Args:
        dataset_path: Path to dataset directory
        parsed_data: List of parsed image data entries
        all_classes: List of unique class names
        iou_threshold: IoU threshold used
        confidence_threshold: Confidence threshold used
        errors: List of errors encountered

    Returns:
        int: The dataset_id of the inserted dataset
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Clear old dataset with same path if exists
        cursor.execute('DELETE FROM dataset_metadata WHERE path = ?', (dataset_path,))

        # Insert dataset metadata
        cursor.execute('''
            INSERT INTO dataset_metadata
            (path, total_images, total_classes, iou_threshold, confidence_threshold)
            VALUES (?, ?, ?, ?, ?)
        ''', (dataset_path, len(parsed_data), len(all_classes), iou_threshold, confidence_threshold))

        dataset_id = cursor.lastrowid

        # Insert classes
        class_id_map = {}
        for class_name in all_classes:
            cursor.execute('''
                INSERT INTO classes (dataset_id, name, total_gt_count, total_pred_count, tp_count, fp_count, fn_count)
                VALUES (?, ?, 0, 0, 0, 0, 0)
            ''', (dataset_id, class_name))
            class_id_map[class_name] = cursor.lastrowid

        # Process each image
        for entry in parsed_data:
            gt_data = entry.get('gt_data')
            pred_data = entry.get('pred_data')

            # Get image dimensions (prefer GT data, fallback to prediction data or open image)
            width = 0
            height = 0
            if gt_data:
                width = gt_data.get('width', 0)
                height = gt_data.get('height', 0)
            elif pred_data:
                width = pred_data.get('width', 0)
                height = pred_data.get('height', 0)

            # If dimensions not found, try to get from image file
            if width == 0 or height == 0:
                try:
                    from PIL import Image
                    with Image.open(entry['image_path']) as img:
                        width, height = img.size
                except:
                    pass

            # Count GT and prediction boxes
            total_gt_boxes = len(gt_data.get('annotations', [])) if gt_data else 0
            total_pred_boxes = len(pred_data.get('predictions', [])) if pred_data else 0

            # Insert image metadata
            cursor.execute('''
                INSERT INTO image_metadata
                (dataset_id, filename, width, height, thumbnail_path, image_path, total_gt_boxes, total_pred_boxes, has_fp, has_fn, is_perfect)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dataset_id, entry['image_filename'], width, height, entry['thumbnail_path'], entry['image_path'], total_gt_boxes, total_pred_boxes, 0, 0, 1))

            image_id = cursor.lastrowid

            # Collect boxes by class
            gt_boxes_by_class = defaultdict(list)
            pred_boxes_by_class = defaultdict(list)

            # Process GT boxes
            if gt_data:
                for idx, ann in enumerate(gt_data.get('annotations', [])):
                    class_name = ann['class']
                    bbox = ann['bbox']
                    class_id = class_id_map[class_name]

                    gt_boxes_by_class[class_name].append(bbox)

                    # Insert GT bounding box
                    cursor.execute('''
                        INSERT INTO bounding_boxes
                        (image_id, class_id, type, x1, y1, x2, y2, confidence, iou, classification)
                        VALUES (?, ?, 'ground_truth', ?, ?, ?, ?, NULL, NULL, NULL)
                    ''', (image_id, class_id, bbox[0], bbox[1], bbox[2], bbox[3]))

            # Process prediction boxes (filter by confidence threshold)
            if pred_data:
                for pred in pred_data.get('predictions', []):
                    if pred['score'] < confidence_threshold:
                        continue  # Skip low confidence predictions

                    class_name = pred['class']
                    bbox = pred['bbox']
                    class_id = class_id_map[class_name]

                    pred_boxes_by_class[class_name].append(bbox)

                    # Insert prediction bounding box
                    cursor.execute('''
                        INSERT INTO bounding_boxes
                        (image_id, class_id, type, x1, y1, x2, y2, confidence, iou, classification)
                        VALUES (?, ?, 'prediction', ?, ?, ?, ?, ?, NULL, NULL)
                    ''', (image_id, class_id, bbox[0], bbox[1], bbox[2], bbox[3], pred['score']))

            # Calculate metrics for each class in this image
            image_has_fp = False
            image_has_fn = False

            for class_name in all_classes:
                class_id = class_id_map[class_name]
                gt_boxes = gt_boxes_by_class[class_name]
                pred_boxes = pred_boxes_by_class[class_name]

                # Classify boxes
                classification = classify_bounding_boxes(gt_boxes, pred_boxes, iou_threshold)

                # Update bounding boxes with classification
                # First, get the IDs of boxes we just inserted
                if classification['tp']:
                    for gt_idx, pred_idx in classification['tp']:
                        # Get the last inserted boxes and update them
                        # For simplicity, we'll just calculate metrics here

                        # Update GT box as TP
                        cursor.execute('''
                            UPDATE bounding_boxes SET classification = 'tp'
                            WHERE image_id = ? AND class_id = ? AND type = 'ground_truth'
                            AND x1 = ? AND y1 = ?
                        ''', (image_id, class_id, gt_boxes[gt_idx][0], gt_boxes[gt_idx][1]))

                        # Get the prediction box IoU
                        iou = calculate_iou(gt_boxes[gt_idx], pred_boxes[pred_idx])

                        # Update prediction box as TP with IoU
                        cursor.execute('''
                            UPDATE bounding_boxes SET classification = 'tp', iou = ?
                            WHERE image_id = ? AND class_id = ? AND type = 'prediction'
                            AND x1 = ? AND y1 = ?
                        ''', (iou, image_id, class_id, pred_boxes[pred_idx][0], pred_boxes[pred_idx][1]))

                if classification['fp']:
                    for pred_idx in classification['fp']:
                        image_has_fp = True
                        cursor.execute('''
                            UPDATE bounding_boxes SET classification = 'fp'
                            WHERE image_id = ? AND class_id = ? AND type = 'prediction'
                            AND x1 = ? AND y1 = ?
                        ''', (image_id, class_id, pred_boxes[pred_idx][0], pred_boxes[pred_idx][1]))

                if classification['fn']:
                    for gt_idx in classification['fn']:
                        image_has_fn = True
                        cursor.execute('''
                            UPDATE bounding_boxes SET classification = 'fn'
                            WHERE image_id = ? AND class_id = ? AND type = 'ground_truth'
                            AND x1 = ? AND y1 = ?
                        ''', (image_id, class_id, gt_boxes[gt_idx][0], gt_boxes[gt_idx][1]))

            # Update image metadata with FP/FN flags
            is_perfect = not (image_has_fp or image_has_fn)
            cursor.execute('''
                UPDATE image_metadata
                SET has_fp = ?, has_fn = ?, is_perfect = ?
                WHERE id = ?
            ''', (int(image_has_fp), int(image_has_fn), int(is_perfect), image_id))

        # Calculate overall metrics for each class
        for class_name, class_id in class_id_map.items():
            # Get all boxes for this class
            cursor.execute('''
                SELECT type, classification
                FROM bounding_boxes
                WHERE class_id = ?
            ''', (class_id,))

            tp_count = 0
            fp_count = 0
            fn_count = 0
            total_gt_count = 0
            total_pred_count = 0

            for row in cursor.fetchall():
                box_type = row[0]
                classification = row[1]

                if box_type == 'ground_truth':
                    total_gt_count += 1
                    if classification == 'fn':
                        fn_count += 1
                elif box_type == 'prediction':
                    total_pred_count += 1
                    if classification == 'fp':
                        fp_count += 1
                    elif classification == 'tp':
                        tp_count += 1

            # Calculate metrics
            metrics = calculate_class_metrics(tp_count, fp_count, fn_count)

            # Update class metrics
            cursor.execute('''
                UPDATE classes
                SET total_gt_count = ?, total_pred_count = ?,
                    tp_count = ?, fp_count = ?, fn_count = ?,
                    recall = ?, precision = ?, fpr = ?, f1_score = ?
                WHERE id = ?
            ''', (
                total_gt_count, total_pred_count,
                tp_count, fp_count, fn_count,
                metrics['recall'], metrics['precision'], metrics['fpr'], metrics['f1_score'],
                class_id
            ))

        conn.commit()

    return dataset_id


def recalculate_statistics(dataset_id: int, iou_threshold: float, confidence_threshold: float) -> Dict[str, Any]:
    """
    Recalculate statistics for a dataset with new thresholds

    Args:
        dataset_id: ID of the dataset to recalculate
        iou_threshold: New IoU threshold for TP/FP classification
        confidence_threshold: New confidence threshold for predictions

    Returns:
        Dictionary containing:
            - success (bool): Whether recalculation was successful
            - classes (list): Array of class statistics with updated metrics
            - overall_metrics (dict): Overall metrics across all classes
            - iou_threshold (float): Updated IoU threshold
            - confidence_threshold (float): Updated confidence threshold
            - errors (list): List of any errors encountered
    """
    errors = []

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Check if dataset exists
            cursor.execute('''
                SELECT id, path
                FROM dataset_metadata
                WHERE id = ?
            ''', (dataset_id,))

            dataset_row = cursor.fetchone()

            if dataset_row is None:
                return {
                    'success': False,
                    'errors': [f'Dataset with ID {dataset_id} not found'],
                    'iou_threshold': iou_threshold,
                    'confidence_threshold': confidence_threshold
                }

            dataset_path = dataset_row[1]

            # Get all images for this dataset
            cursor.execute('''
                SELECT id, filename
                FROM image_metadata
                WHERE dataset_id = ?
                ORDER BY id
            ''', (dataset_id,))

            image_rows = cursor.fetchall()

            # Get all classes for this dataset
            cursor.execute('''
                SELECT id, name
                FROM classes
                WHERE dataset_id = ?
                ORDER BY name
            ''', (dataset_id,))

            class_rows = cursor.fetchall()
            class_id_map = {row[1]: {'id': row[0], 'name': row[1]} for row in class_rows}

            # Process each image
            for image_id, filename in image_rows:
                # Get all bounding boxes for this image
                cursor.execute('''
                    SELECT bb.id, bb.class_id, bb.type, bb.x1, bb.y1, bb.x2, bb.y2, bb.confidence, c.name
                    FROM bounding_boxes bb
                    JOIN classes c ON bb.class_id = c.id
                    WHERE bb.image_id = ?
                    ORDER BY bb.id
                ''', (image_id,))

                bbox_rows = cursor.fetchall()

                # Separate GT and prediction boxes by class
                gt_boxes_by_class = defaultdict(list)
                pred_boxes_by_class = defaultdict(list)
                bbox_ids_by_class = defaultdict(list)  # Store bbox IDs for updating

                for bbox_id, class_id, bbox_type, x1, y1, x2, y2, confidence, class_name in bbox_rows:

                    if bbox_type == 'ground_truth':
                        gt_boxes_by_class[class_name].append((x1, y1, x2, y2))
                        bbox_ids_by_class[class_name].append({'id': bbox_id, 'type': 'gt', 'coords': (x1, y1, x2, y2)})
                    elif bbox_type == 'prediction':
                        # Filter by confidence threshold
                        if confidence is None or confidence >= confidence_threshold:
                            pred_boxes_by_class[class_name].append((x1, y1, x2, y2))
                            bbox_ids_by_class[class_name].append({'id': bbox_id, 'type': 'pred', 'coords': (x1, y1, x2, y2), 'confidence': confidence})

                # Reset classification for all boxes
                for bbox_info in [item for sublist in bbox_ids_by_class.values() for item in sublist]:
                    cursor.execute('''
                        UPDATE bounding_boxes
                        SET classification = NULL, iou = NULL
                        WHERE id = ?
                    ''', (bbox_info['id'],))

                # Recalculate classifications for each class
                image_has_fp = False
                image_has_fn = False

                for class_name, class_info in class_id_map.items():
                    gt_boxes = gt_boxes_by_class[class_name]
                    pred_boxes = pred_boxes_by_class[class_name]
                    class_id = class_info['id']

                    # Classify boxes with new threshold
                    classification = classify_bounding_boxes(gt_boxes, pred_boxes, iou_threshold)

                    # Update bounding boxes with new classifications and IoU values
                    # True Positives
                    for gt_idx, pred_idx in classification['tp']:
                        # Find corresponding bbox IDs and update them
                        gt_coords = gt_boxes[gt_idx]
                        pred_coords = pred_boxes[pred_idx]

                        # Update GT box as TP
                        cursor.execute('''
                            UPDATE bounding_boxes
                            SET classification = 'tp'
                            WHERE image_id = ? AND class_id = ? AND type = 'ground_truth'
                            AND x1 = ? AND y1 = ? AND x2 = ? AND y2 = ?
                        ''', (image_id, class_id, gt_coords[0], gt_coords[1], gt_coords[2], gt_coords[3]))

                        # Calculate and update prediction box with IoU
                        iou = calculate_iou(gt_coords, pred_coords)
                        cursor.execute('''
                            UPDATE bounding_boxes
                            SET classification = 'tp', iou = ?
                            WHERE image_id = ? AND class_id = ? AND type = 'prediction'
                            AND x1 = ? AND y1 = ? AND x2 = ? AND y2 = ?
                        ''', (iou, image_id, class_id, pred_coords[0], pred_coords[1], pred_coords[2], pred_coords[3]))

                    # False Positives
                    for pred_idx in classification['fp']:
                        image_has_fp = True
                        pred_coords = pred_boxes[pred_idx]
                        cursor.execute('''
                            UPDATE bounding_boxes
                            SET classification = 'fp'
                            WHERE image_id = ? AND class_id = ? AND type = 'prediction'
                            AND x1 = ? AND y1 = ? AND x2 = ? AND y2 = ?
                        ''', (image_id, class_id, pred_coords[0], pred_coords[1], pred_coords[2], pred_coords[3]))

                    # False Negatives
                    for gt_idx in classification['fn']:
                        image_has_fn = True
                        gt_coords = gt_boxes[gt_idx]
                        cursor.execute('''
                            UPDATE bounding_boxes
                            SET classification = 'fn'
                            WHERE image_id = ? AND class_id = ? AND type = 'ground_truth'
                            AND x1 = ? AND y1 = ? AND x2 = ? AND y2 = ?
                        ''', (image_id, class_id, gt_coords[0], gt_coords[1], gt_coords[2], gt_coords[3]))

            # Update dataset metadata with new thresholds
            cursor.execute('''
                UPDATE dataset_metadata
                SET iou_threshold = ?, confidence_threshold = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (iou_threshold, confidence_threshold, dataset_id))

            # Recalculate metrics for each class
            classes_data = []
            overall_tp = 0
            overall_fp = 0
            overall_fn = 0
            total_gt = 0
            total_pred = 0

            for class_name, class_info in class_id_map.items():
                class_id = class_info['id']

                # Get all boxes for this class
                cursor.execute('''
                    SELECT type, classification
                    FROM bounding_boxes
                    WHERE class_id = ?
                ''', (class_id,))

                tp_count = 0
                fp_count = 0
                fn_count = 0
                total_gt_count = 0
                total_pred_count = 0

                for row in cursor.fetchall():
                    box_type = row[0]
                    classification = row[1]

                    if box_type == 'ground_truth':
                        total_gt_count += 1
                        if classification == 'fn':
                            fn_count += 1
                    elif box_type == 'prediction':
                        total_pred_count += 1
                        if classification == 'fp':
                            fp_count += 1
                        elif classification == 'tp':
                            tp_count += 1

                # Calculate metrics
                metrics = calculate_class_metrics(tp_count, fp_count, fn_count)

                # Update class metrics in database
                cursor.execute('''
                    UPDATE classes
                    SET total_gt_count = ?, total_pred_count = ?,
                        tp_count = ?, fp_count = ?, fn_count = ?,
                        recall = ?, precision = ?, fpr = ?, f1_score = ?
                    WHERE id = ?
                ''', (
                    total_gt_count, total_pred_count,
                    tp_count, fp_count, fn_count,
                    metrics['recall'], metrics['precision'], metrics['fpr'], metrics['f1_score'],
                    class_id
                ))

                # Add to classes_data
                classes_data.append({
                    'id': class_id,
                    'name': class_name,
                    'total_gt_count': total_gt_count,
                    'total_pred_count': total_pred_count,
                    'tp_count': tp_count,
                    'fp_count': fp_count,
                    'fn_count': fn_count,
                    'recall': metrics['recall'],
                    'precision': metrics['precision'],
                    'fpr': metrics['fpr'],
                    'f1_score': metrics['f1_score']
                })

                # Accumulate for overall metrics
                overall_tp += tp_count
                overall_fp += fp_count
                overall_fn += fn_count
                total_gt += total_gt_count
                total_pred += total_pred_count

            # Calculate overall metrics
            if (overall_tp + overall_fn) > 0:
                overall_recall = overall_tp / (overall_tp + overall_fn)
            else:
                overall_recall = 0.0

            if (overall_tp + overall_fp) > 0:
                overall_precision = overall_tp / (overall_tp + overall_fp)
            else:
                overall_precision = 0.0

            if (overall_precision + overall_recall) > 0:
                overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall)
            else:
                overall_f1 = 0.0

            if (overall_fp + overall_tp) > 0:
                overall_fpr = overall_fp / (overall_fp + overall_tp)
            else:
                overall_fpr = 0.0

            overall_metrics = {
                'total_gt_boxes': total_gt,
                'total_pred_boxes': total_pred,
                'total_tp': overall_tp,
                'total_fp': overall_fp,
                'total_fn': overall_fn,
                'recall': overall_recall,
                'precision': overall_precision,
                'fpr': overall_fpr,
                'f1_score': overall_f1
            }

            conn.commit()

            return {
                'success': True,
                'classes': classes_data,
                'overall_metrics': overall_metrics,
                'iou_threshold': iou_threshold,
                'confidence_threshold': confidence_threshold,
                'errors': errors
            }

    except Exception as e:
        return {
            'success': False,
            'errors': [str(e)],
            'iou_threshold': iou_threshold,
            'confidence_threshold': confidence_threshold
        }


if __name__ == "__main__":
    # Test dataset loading
    import sys

    print("=" * 60)
    print("Dataset Loader Test")
    print("=" * 60)

    test_dataset_path = './test_dataset' if len(sys.argv) < 2 else sys.argv[1]
    test_iou_threshold = 0.5 if len(sys.argv) < 3 else float(sys.argv[2])

    print(f"\nDataset Path: {test_dataset_path}")
    print(f"IoU Threshold: {test_iou_threshold}\n")

    result = load_dataset(test_dataset_path, test_iou_threshold)

    print("=" * 60)
    print("Loading Result")
    print("=" * 60)

    if result['success']:
        print(f"\n✓ Dataset loaded successfully")
        print(f"  Dataset ID: {result['dataset_id']}")
        print(f"  Total Images: {result['total_images']}")
        print(f"  Total Classes: {result['total_classes']}")

        if result['errors']:
            print(f"\nWarnings/Errors:")
            for error in result['errors'][:10]:  # Show first 10
                print(f"  - {error}")
            if len(result['errors']) > 10:
                print(f"  ... and {len(result['errors']) - 10} more")
    else:
        print(f"\n✗ Dataset loading failed")
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")

    print("=" * 60)
