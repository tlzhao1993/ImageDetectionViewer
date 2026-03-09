"""
Metrics calculation module for Image Detection Result Analyzer
Handles IoU calculation, bounding box matching, and metric calculations
"""
from typing import Tuple, List, Dict, Any, Optional


def calculate_iou(box1: Tuple[float, float, float, float],
                  box2: Tuple[float, float, float, float]) -> float:
    """
    Calculate Intersection over Union (IoU) for two bounding boxes

    Args:
        box1: First bounding box as (x1, y1, x2, y2) coordinates
        box2: Second bounding box as (x1, y1, x2, y2) coordinates

    Returns:
        IoU value between 0.0 and 1.0
        - 1.0: Boxes perfectly overlap
        - 0.0: Boxes do not overlap

    Note:
        Bounding box coordinates are in format (x1, y1, x2, y2) where:
        - (x1, y1) is top-left corner
        - (x2, y2) is bottom-right corner
    """
    # Unpack box coordinates
    x1_min, y1_min, x1_max, y1_max = box1
    x2_min, y2_min, x2_max, y2_max = box2

    # Calculate intersection coordinates
    intersection_x1 = max(x1_min, x2_min)
    intersection_y1 = max(y1_min, y2_min)
    intersection_x2 = min(x1_max, x2_max)
    intersection_y2 = min(y1_max, y2_max)

    # Calculate intersection area
    intersection_width = max(0.0, intersection_x2 - intersection_x1)
    intersection_height = max(0.0, intersection_y2 - intersection_y1)
    intersection_area = intersection_width * intersection_height

    # Calculate area of each box
    box1_area = (x1_max - x1_min) * (y1_max - y1_min)
    box2_area = (x2_max - x2_min) * (y2_max - y2_min)

    # Calculate union area
    union_area = box1_area + box2_area - intersection_area

    # Handle edge case where union is 0
    if union_area == 0:
        return 0.0

    # Calculate IoU
    iou = intersection_area / union_area

    return iou


def classify_bounding_boxes(gt_boxes: List[Tuple[float, float, float, float]],
                          pred_boxes: List[Tuple[float, float, float, float]],
                          iou_threshold: float = 0.5) -> Dict[str, List[Tuple]]:
    """
    Classify bounding boxes as TP, FP, or FN based on IoU threshold

    Args:
        gt_boxes: List of ground truth bounding boxes as (x1, y1, x2, y2) coordinates
        pred_boxes: List of prediction bounding boxes as (x1, y1, x2, y2) coordinates
        iou_threshold: IoU threshold for considering a prediction as TP (default: 0.5)

    Returns:
        Dictionary containing:
        - tp: List of tuples (gt_index, pred_index) for true positives
        - fp: List of pred_index for false positives
        - fn: List of gt_index for false negatives
    """
    # Track which boxes have been matched
    gt_matched = [False] * len(gt_boxes)
    pred_matched = [False] * len(pred_boxes)

    # Find matches (TP)
    tp = []
    for pred_idx, pred_box in enumerate(pred_boxes):
        best_iou = 0.0
        best_gt_idx = -1

        for gt_idx, gt_box in enumerate(gt_boxes):
            if gt_matched[gt_idx]:
                continue  # This GT box is already matched

            iou = calculate_iou(gt_box, pred_box)
            if iou > best_iou:
                best_iou = iou
                best_gt_idx = gt_idx

        # Check if this prediction meets the threshold
        if best_iou >= iou_threshold and best_gt_idx != -1:
            tp.append((best_gt_idx, pred_idx))
            gt_matched[best_gt_idx] = True
            pred_matched[pred_idx] = True

    # Find false positives (predictions without matching GT)
    fp = [idx for idx, matched in enumerate(pred_matched) if not matched]

    # Find false negatives (GT boxes without matching predictions)
    fn = [idx for idx, matched in enumerate(gt_matched) if not matched]

    return {
        'tp': tp,
        'fp': fp,
        'fn': fn
    }


def calculate_class_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """
    Calculate recall, precision, FPR, and F1 score for a class

    Args:
        tp: Number of true positives
        fp: Number of false positives
        fn: Number of false negatives

    Returns:
        Dictionary containing:
        - recall: TP / (TP + FN)
        - precision: TP / (TP + FP)
        - fpr: FP / (FP + TN) [Note: TN is not available in object detection context]
        - f1_score: 2 * (precision * recall) / (precision + recall)

    Note:
        FPR (False Positive Rate) in object detection context is typically calculated
        as FP / (FP + TN), but TN (True Negatives) is often undefined or infinite
        in object detection. Some implementations use FP / (FP + TP) or other metrics.
        Here we calculate it as FP / (FP + TP) for simplicity.
    """
    metrics = {}

    # Calculate recall (True Positive Rate)
    if (tp + fn) > 0:
        metrics['recall'] = tp / (tp + fn)
    else:
        metrics['recall'] = 0.0

    # Calculate precision
    if (tp + fp) > 0:
        metrics['precision'] = tp / (tp + fp)
    else:
        metrics['precision'] = 0.0

    # Calculate FPR (False Positive Rate)
    # In object detection, TN is often undefined. We use FP / (FP + TP) as an alternative
    if (fp + tp) > 0:
        metrics['fpr'] = fp / (fp + tp)
    else:
        metrics['fpr'] = 0.0

    # Calculate F1 Score
    if metrics['precision'] + metrics['recall'] > 0:
        metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / \
                             (metrics['precision'] + metrics['recall'])
    else:
        metrics['f1_score'] = 0.0

    return metrics


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("IoU Calculation Test")
    print("=" * 60)

    # Test 1: Perfectly overlapping boxes (IoU should be 1.0)
    print("\n" + "-" * 60)
    print("Test 1: Perfectly overlapping boxes")
    print("-" * 60)
    box1 = (100, 200, 300, 400)
    box2 = (100, 200, 300, 400)
    iou = calculate_iou(box1, box2)
    print(f"Box 1: {box1}")
    print(f"Box 2: {box2}")
    print(f"IoU: {iou:.6f}")
    if abs(iou - 1.0) < 0.001:
        print("✓ PASS: IoU is 1.0 as expected")
    else:
        print(f"✗ FAIL: Expected IoU = 1.0, got {iou:.6f}")

    # Test 2: Non-overlapping boxes (IoU should be 0.0)
    print("\n" + "-" * 60)
    print("Test 2: Non-overlapping boxes")
    print("-" * 60)
    box1 = (100, 200, 300, 400)
    box2 = (500, 600, 700, 800)
    iou = calculate_iou(box1, box2)
    print(f"Box 1: {box1}")
    print(f"Box 2: {box2}")
    print(f"IoU: {iou:.6f}")
    if abs(iou - 0.0) < 0.001:
        print("✓ PASS: IoU is 0.0 as expected")
    else:
        print(f"✗ FAIL: Expected IoU = 0.0, got {iou:.6f}")

    # Test 3: Partially overlapping boxes
    print("\n" + "-" * 60)
    print("Test 3: Partially overlapping boxes")
    print("-" * 60)
    box1 = (100, 200, 300, 400)
    box2 = (200, 300, 400, 500)
    iou = calculate_iou(box1, box2)
    print(f"Box 1: {box1}")
    print(f"Box 2: {box2}")
    print(f"IoU: {iou:.6f}")
    if 0.0 < iou < 1.0:
        print(f"✓ PASS: IoU is between 0.0 and 1.0 as expected")
    else:
        print(f"✗ FAIL: Expected IoU between 0.0 and 1.0, got {iou:.6f}")

    # Additional test: Slightly offset boxes
    print("\n" + "-" * 60)
    print("Test 4: Slightly offset boxes")
    print("-" * 60)
    box1 = (0, 0, 100, 100)
    box2 = (10, 10, 110, 110)
    iou = calculate_iou(box1, box2)
    print(f"Box 1: {box1}")
    print(f"Box 2: {box2}")
    print(f"IoU: {iou:.6f}")
    # Expected IoU for this case:
    # Box 1 area: 100 * 100 = 10000
    # Box 2 area: 100 * 100 = 10000
    # Intersection: (10, 10, 100, 100) = 90 * 90 = 8100
    # Union: 10000 + 10000 - 8100 = 11900
    # IoU: 8100 / 11900 ≈ 0.6807
    expected_iou = 8100.0 / 11900.0
    if abs(iou - expected_iou) < 0.001:
        print(f"✓ PASS: IoU matches expected value {expected_iou:.6f}")
    else:
        print(f"✗ FAIL: Expected IoU = {expected_iou:.6f}, got {iou:.6f}")

    # Test bounding box classification
    print("\n" + "=" * 60)
    print("Bounding Box Classification Test")
    print("=" * 60)

    gt_boxes = [
        (100, 200, 300, 400),  # GT box 1
        (500, 600, 700, 800),  # GT box 2
        (1000, 100, 1200, 300),  # GT box 3 (no match)
    ]

    pred_boxes = [
        (95, 195, 305, 405),  # Pred box 1 - matches GT box 1 (IoU ≈ 0.91)
        (495, 595, 705, 805),  # Pred box 2 - matches GT box 2 (IoU ≈ 0.91)
        (800, 900, 900, 1000),  # Pred box 3 - no match (FP)
    ]

    print(f"\nGround Truth Boxes: {len(gt_boxes)}")
    for idx, box in enumerate(gt_boxes, 1):
        print(f"  GT {idx}: {box}")

    print(f"\nPrediction Boxes: {len(pred_boxes)}")
    for idx, box in enumerate(pred_boxes, 1):
        print(f"  Pred {idx}: {box}")

    result = classify_bounding_boxes(gt_boxes, pred_boxes, iou_threshold=0.5)

    print(f"\nClassification Results:")
    print(f"  True Positives (TP): {len(result['tp'])}")
    for gt_idx, pred_idx in result['tp']:
        iou = calculate_iou(gt_boxes[gt_idx], pred_boxes[pred_idx])
        print(f"    GT {gt_idx+1} <-> Pred {pred_idx+1} (IoU: {iou:.4f})")

    print(f"  False Positives (FP): {len(result['fp'])}")
    for pred_idx in result['fp']:
        print(f"    Pred {pred_idx+1} (no matching GT)")

    print(f"  False Negatives (FN): {len(result['fn'])}")
    for gt_idx in result['fn']:
        print(f"    GT {gt_idx+1} (no matching prediction)")

    # Test metric calculations
    print("\n" + "=" * 60)
    print("Metric Calculation Test")
    print("=" * 60)

    # Test case 1: Good precision, good recall
    print("\nTest 1: Good precision, good recall")
    tp, fp, fn = 80, 10, 15
    metrics = calculate_class_metrics(tp, fp, fn)
    print(f"  TP={tp}, FP={fp}, FN={fn}")
    print(f"  Recall: {metrics['recall']:.4f} (Expected: {tp/(tp+fn):.4f})")
    print(f"  Precision: {metrics['precision']:.4f} (Expected: {tp/(tp+fp):.4f})")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")

    # Test case 2: Perfect recall, poor precision
    print("\nTest 2: Perfect recall, poor precision")
    tp, fp, fn = 50, 50, 0
    metrics = calculate_class_metrics(tp, fp, fn)
    print(f"  TP={tp}, FP={fp}, FN={fn}")
    print(f"  Recall: {metrics['recall']:.4f} (Expected: 1.0000)")
    print(f"  Precision: {metrics['precision']:.4f} (Expected: 0.5000)")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")

    # Test case 3: No predictions
    print("\nTest 3: No predictions")
    tp, fp, fn = 0, 0, 10
    metrics = calculate_class_metrics(tp, fp, fn)
    print(f"  TP={tp}, FP={fp}, FN={fn}")
    print(f"  Recall: {metrics['recall']:.4f} (Expected: 0.0000)")
    print(f"  Precision: {metrics['precision']:.4f} (Expected: 0.0000)")
    print(f"  F1 Score: {metrics['f1_score']:.4f}")

    print("\n" + "=" * 60)
