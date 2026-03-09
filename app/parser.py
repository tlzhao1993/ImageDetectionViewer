"""
JSON parsing module for Image Detection Result Analyzer
Handles parsing of ground truth and prediction JSON files
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


def parse_ground_truth_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a ground truth JSON annotation file

    Args:
        file_path: Path to the ground truth JSON file

    Returns:
        Dictionary containing:
        - filename (str): Image filename
        - width (int): Image width
        - height (int): Image height
        - annotations (list): List of annotation dictionaries with:
            - class (str): Class name
            - bbox (tuple): (x1, y1, x2, y2) coordinates

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If required fields are missing
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Read and parse JSON file
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ['filename', 'width', 'height', 'annotations']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in ground truth file: {field}")

    # Validate annotations is a list
    if not isinstance(data['annotations'], list):
        raise ValueError("Annotations must be a list")

    # Parse annotations
    parsed_annotations = []
    for idx, ann in enumerate(data['annotations']):
        if not isinstance(ann, dict):
            raise ValueError(f"Annotation at index {idx} is not a dictionary")

        # Validate annotation fields
        if 'class' not in ann:
            raise ValueError(f"Annotation at index {idx} missing 'class' field")

        if 'bbox' not in ann:
            raise ValueError(f"Annotation at index {idx} missing 'bbox' field")

        # Validate bbox is a list/tuple with 4 elements
        bbox = ann['bbox']
        if not isinstance(bbox, (list, tuple)):
            raise ValueError(f"Annotation at index {idx} bbox is not a list/tuple")

        if len(bbox) != 4:
            raise ValueError(f"Annotation at index {idx} bbox must have 4 elements (x1, y1, x2, y2)")

        # Validate bbox coordinates are numeric
        try:
            x1, y1, x2, y2 = [float(coord) for coord in bbox]
        except (ValueError, TypeError):
            raise ValueError(f"Annotation at index {idx} bbox coordinates must be numeric")

        # Validate bbox coordinates are non-negative
        if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
            raise ValueError(f"Annotation at index {idx} bbox coordinates must be non-negative")

        # Validate x2 > x1 and y2 > y1
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Annotation at index {idx} bbox has invalid dimensions (x2 <= x1 or y2 <= y1)")

        parsed_annotations.append({
            'class': ann['class'],
            'bbox': (x1, y1, x2, y2)
        })

    return {
        'filename': data['filename'],
        'width': int(data['width']),
        'height': int(data['height']),
        'annotations': parsed_annotations
    }


def parse_prediction_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a prediction JSON file with confidence scores

    Args:
        file_path: Path to the prediction JSON file

    Returns:
        Dictionary containing:
        - filename (str): Image filename
        - width (int): Image width
        - height (int): Image height
        - predictions (list): List of prediction dictionaries with:
            - class (str): Class name
            - bbox (tuple): (x1, y1, x2, y2) coordinates
            - score (float): Confidence score

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If required fields are missing
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Prediction file not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Read and parse JSON file
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Validate required fields
    required_fields = ['filename', 'width', 'height', 'predictions']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in prediction file: {field}")

    # Validate predictions is a list
    if not isinstance(data['predictions'], list):
        raise ValueError("Predictions must be a list")

    # Parse predictions
    parsed_predictions = []
    for idx, pred in enumerate(data['predictions']):
        if not isinstance(pred, dict):
            raise ValueError(f"Prediction at index {idx} is not a dictionary")

        # Validate prediction fields
        if 'class' not in pred:
            raise ValueError(f"Prediction at index {idx} missing 'class' field")

        if 'bbox' not in pred:
            raise ValueError(f"Prediction at index {idx} missing 'bbox' field")

        if 'score' not in pred:
            raise ValueError(f"Prediction at index {idx} missing 'score' field")

        # Validate bbox is a list/tuple with 4 elements
        bbox = pred['bbox']
        if not isinstance(bbox, (list, tuple)):
            raise ValueError(f"Prediction at index {idx} bbox is not a list/tuple")

        if len(bbox) != 4:
            raise ValueError(f"Prediction at index {idx} bbox must have 4 elements (x1, y1, x2, y2)")

        # Validate bbox coordinates are numeric
        try:
            x1, y1, x2, y2 = [float(coord) for coord in bbox]
        except (ValueError, TypeError):
            raise ValueError(f"Prediction at index {idx} bbox coordinates must be numeric")

        # Validate bbox coordinates are non-negative
        if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
            raise ValueError(f"Prediction at index {idx} bbox coordinates must be non-negative")

        # Validate x2 > x1 and y2 > y1
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Prediction at index {idx} bbox has invalid dimensions (x2 <= x1 or y2 <= y1)")

        # Validate score is numeric and in range [0, 1]
        try:
            score = float(pred['score'])
        except (ValueError, TypeError):
            raise ValueError(f"Prediction at index {idx} score must be numeric")

        if score < 0 or score > 1:
            raise ValueError(f"Prediction at index {idx} score must be in range [0, 1]")

        parsed_predictions.append({
            'class': pred['class'],
            'bbox': (x1, y1, x2, y2),
            'score': score
        })

    return {
        'filename': data['filename'],
        'width': int(data['width']),
        'height': int(data['height']),
        'predictions': parsed_predictions
    }


def get_unique_classes_from_gt(gt_data: Dict[str, Any]) -> List[str]:
    """
    Extract unique class names from ground truth data

    Args:
        gt_data: Parsed ground truth data from parse_ground_truth_file

    Returns:
        List of unique class names
    """
    classes = set()
    for ann in gt_data.get('annotations', []):
        if 'class' in ann:
            classes.add(ann['class'])
    return sorted(list(classes))


def get_unique_classes_from_pred(pred_data: Dict[str, Any]) -> List[str]:
    """
    Extract unique class names from prediction data

    Args:
        pred_data: Parsed prediction data from parse_prediction_file

    Returns:
        List of unique class names
    """
    classes = set()
    for pred in pred_data.get('predictions', []):
        if 'class' in pred:
            classes.add(pred['class'])
    return sorted(list(classes))


if __name__ == "__main__":
    # Test parsing functions with sample data
    import sys

    # Create test directory structure
    test_dir = Path('test_dataset')
    test_dir.mkdir(exist_ok=True)
    (test_dir / 'gt').mkdir(exist_ok=True)
    (test_dir / 'predictions').mkdir(exist_ok=True)

    # Create sample ground truth file
    gt_sample = {
        "filename": "test_image.jpg",
        "width": 1920,
        "height": 1080,
        "annotations": [
            {
                "class": "car",
                "bbox": [100, 200, 300, 400]
            },
            {
                "class": "person",
                "bbox": [500, 600, 700, 800]
            },
            {
                "class": "car",
                "bbox": [1000, 100, 1200, 300]
            }
        ]
    }

    gt_file = test_dir / 'gt' / 'test_image.json'
    with open(gt_file, 'w') as f:
        json.dump(gt_sample, f, indent=2)

    print("=" * 60)
    print("Ground Truth Parsing Test")
    print("=" * 60)
    print(f"\nCreated sample GT file: {gt_file}")

    try:
        gt_data = parse_ground_truth_file(str(gt_file))
        print(f"\n✓ File parsed successfully")
        print(f"  Filename: {gt_data['filename']}")
        print(f"  Dimensions: {gt_data['width']}x{gt_data['height']}")
        print(f"  Total annotations: {len(gt_data['annotations'])}")
        print(f"\n  Annotations:")
        for idx, ann in enumerate(gt_data['annotations'], 1):
            print(f"    {idx}. Class: {ann['class']}, BBox: {ann['bbox']}")

        # Extract unique classes
        classes = get_unique_classes_from_gt(gt_data)
        print(f"\n  Unique classes: {classes}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

    # Create sample prediction file
    pred_sample = {
        "filename": "test_image.jpg",
        "width": 1920,
        "height": 1080,
        "predictions": [
            {
                "class": "car",
                "bbox": [95, 195, 305, 405],
                "score": 0.95
            },
            {
                "class": "person",
                "bbox": [495, 595, 705, 805],
                "score": 0.88
            },
            {
                "class": "bicycle",
                "bbox": [800, 900, 900, 1000],
                "score": 0.72
            }
        ]
    }

    pred_file = test_dir / 'predictions' / 'test_image_pred.json'
    with open(pred_file, 'w') as f:
        json.dump(pred_sample, f, indent=2)

    print("\n" + "=" * 60)
    print("Prediction Parsing Test")
    print("=" * 60)
    print(f"\nCreated sample prediction file: {pred_file}")

    try:
        pred_data = parse_prediction_file(str(pred_file))
        print(f"\n✓ File parsed successfully")
        print(f"  Filename: {pred_data['filename']}")
        print(f"  Dimensions: {pred_data['width']}x{pred_data['height']}")
        print(f"  Total predictions: {len(pred_data['predictions'])}")
        print(f"\n  Predictions:")
        for idx, pred in enumerate(pred_data['predictions'], 1):
            print(f"    {idx}. Class: {pred['class']}, BBox: {pred['bbox']}, Score: {pred['score']:.3f}")

        # Extract unique classes
        classes = get_unique_classes_from_pred(pred_data)
        print(f"\n  Unique classes: {classes}")

    except Exception as e:
        print(f"\n✗ Error: {e}")

    print("\n" + "=" * 60)
