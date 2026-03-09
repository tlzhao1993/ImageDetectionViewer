"""
Dataset validation module for Image Detection Result Analyzer
Handles validation of dataset directory structure and files
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple


def validate_dataset(dataset_path: str) -> Dict[str, any]:
    """
    Validate dataset directory structure

    Checks for required directories and provides detailed error information

    Args:
        dataset_path: Path to the dataset directory

    Returns:
        Dictionary with:
        - valid (bool): Whether the dataset is valid
        - errors (list): List of error messages if invalid
        - path (str): The validated dataset path
    """
    errors = []

    # Convert to Path object for easier handling
    path = Path(dataset_path)

    # Check if path exists
    if not path.exists():
        errors.append(f"Dataset path does not exist: {dataset_path}")
        return {
            'valid': False,
            'errors': errors,
            'path': dataset_path
        }

    # Check if path is a directory
    if not path.is_dir():
        errors.append(f"Dataset path is not a directory: {dataset_path}")
        return {
            'valid': False,
            'errors': errors,
            'path': dataset_path
        }

    # Check for required directories
    required_dirs = ['images', 'gt', 'predictions']
    for dir_name in required_dirs:
        dir_path = path / dir_name
        if not dir_path.exists():
            errors.append(f"Required directory missing: {dir_name}/")
        elif not dir_path.is_dir():
            errors.append(f"Path exists but is not a directory: {dir_name}/")

    # Check if images directory has any images
    images_dir = path / 'images'
    if images_dir.exists() and images_dir.is_dir():
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        image_files = [
            f for f in images_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        if len(image_files) == 0:
            errors.append("No image files found in images/ directory")

    # Check if gt directory has any JSON files
    gt_dir = path / 'gt'
    if gt_dir.exists() and gt_dir.is_dir():
        json_files = [
            f for f in gt_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        ]
        if len(json_files) == 0:
            errors.append("No JSON files found in gt/ directory")

    # Check if predictions directory has any JSON files
    pred_dir = path / 'predictions'
    if pred_dir.exists() and pred_dir.is_dir():
        json_files = [
            f for f in pred_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        ]
        if len(json_files) == 0:
            errors.append("No JSON files found in predictions/ directory")

    # Check for file matching between images and annotations
    if len(errors) == 0:
        # Get image filenames without extensions
        image_stems = {
            f.stem for f in images_dir.iterdir()
            if f.is_file() and f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        }

        # Get GT JSON filenames without extensions
        gt_stems = {
            f.stem.replace('_gt', '').replace('_pred', '') for f in gt_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        }

        # Get prediction JSON filenames without extensions
        pred_stems = {
            f.stem.replace('_gt', '').replace('_pred', '') for f in pred_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        }

        # Check for mismatched files
        missing_gt = image_stems - gt_stems
        missing_pred = image_stems - pred_stems

        if len(missing_gt) > 0:
            errors.append(
                f"Ground truth annotations missing for {len(missing_gt)} image(s): "
                f"{', '.join(list(missing_gt)[:5])}{'...' if len(missing_gt) > 5 else ''}"
            )

        if len(missing_pred) > 0:
            errors.append(
                f"Prediction files missing for {len(missing_pred)} image(s): "
                f"{', '.join(list(missing_pred)[:5])}{'...' if len(missing_pred) > 5 else ''}"
            )

        # Check for orphaned annotation files (no corresponding image)
        orphaned_gt = gt_stems - image_stems
        orphaned_pred = pred_stems - image_stems

        if len(orphaned_gt) > 0:
            errors.append(
                f"Orphaned ground truth files (no corresponding image): {len(orphaned_gt)} file(s)"
            )

        if len(orphaned_pred) > 0:
            errors.append(
                f"Orphaned prediction files (no corresponding image): {len(orphaned_pred)} file(s)"
            )

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'path': str(path.absolute())
    }


def get_dataset_info(dataset_path: str) -> Dict[str, any]:
    """
    Get basic information about the dataset

    Args:
        dataset_path: Path to the dataset directory

    Returns:
        Dictionary with dataset information
    """
    path = Path(dataset_path)

    info = {
        'path': str(path.absolute()),
        'exists': path.exists(),
        'is_directory': path.is_dir(),
        'total_images': 0,
        'total_gt_files': 0,
        'total_pred_files': 0,
        'directory_structure': {}
    }

    if not path.exists() or not path.is_dir():
        return info

    # Check for required directories
    required_dirs = ['images', 'gt', 'predictions']
    for dir_name in required_dirs:
        dir_path = path / dir_name
        info['directory_structure'][dir_name] = {
            'exists': dir_path.exists(),
            'is_directory': dir_path.is_dir() if dir_path.exists() else False
        }

    # Count images
    images_dir = path / 'images'
    if images_dir.exists() and images_dir.is_dir():
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        info['total_images'] = len([
            f for f in images_dir.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ])

    # Count GT files
    gt_dir = path / 'gt'
    if gt_dir.exists() and gt_dir.is_dir():
        info['total_gt_files'] = len([
            f for f in gt_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        ])

    # Count prediction files
    pred_dir = path / 'predictions'
    if pred_dir.exists() and pred_dir.is_dir():
        info['total_pred_files'] = len([
            f for f in pred_dir.iterdir()
            if f.is_file() and f.suffix.lower() == '.json'
        ])

    return info


if __name__ == "__main__":
    # Test validation functions
    import sys

    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    else:
        test_path = './dataset'

    print("=" * 60)
    print("Dataset Validation Test")
    print("=" * 60)
    print(f"\nTesting path: {test_path}\n")

    # Get dataset info
    info = get_dataset_info(test_path)
    print("Dataset Info:")
    print(f"  Path: {info['path']}")
    print(f"  Exists: {info['exists']}")
    print(f"  Is Directory: {info['is_directory']}")
    print(f"  Total Images: {info['total_images']}")
    print(f"  Total GT Files: {info['total_gt_files']}")
    print(f"  Total Prediction Files: {info['total_pred_files']}")
    print("\nDirectory Structure:")
    for dir_name, dir_info in info['directory_structure'].items():
        status = "✓" if dir_info['exists'] else "✗"
        print(f"  {status} {dir_name}/: {'Exists' if dir_info['exists'] else 'Missing'}")

    # Validate dataset
    print("\n" + "=" * 60)
    result = validate_dataset(test_path)
    print(f"\nValidation Result: {'✓ VALID' if result['valid'] else '✗ INVALID'}")

    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
    else:
        print("\nNo errors found. Dataset is ready to load.")

    print("=" * 60)
