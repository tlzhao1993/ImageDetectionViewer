"""
Script to fix prediction JSON files that use 'name' instead of 'class' field
"""
import os
import json
from pathlib import Path

def fix_prediction_file(file_path: str) -> bool:
    """
    Fix a single prediction JSON file by replacing 'name' with 'class' in predictions

    Args:
        file_path: Path to the prediction JSON file

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if the file uses 'name' instead of 'class'
        if 'predictions' in data:
            modified = False
            for pred in data['predictions']:
                if 'name' in pred and 'class' not in pred:
                    pred['class'] = pred.pop('name')
                    modified = True

            if modified:
                # Write back the fixed data
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """
    Main function to fix all prediction JSON files in a directory
    """
    # Get the predictions directory path
    dataset_path = input("Enter the dataset path (default: /home/tlzhao/Downloads/20260310演示平台数据): ").strip()
    if not dataset_path:
        dataset_path = "/home/tlzhao/Downloads/20260310演示平台数据"

    predictions_dir = Path(dataset_path) / "predictions"

    if not predictions_dir.exists():
        print(f"Error: Predictions directory not found: {predictions_dir}")
        return

    # Get all JSON files
    json_files = list(predictions_dir.glob("*.json"))

    if len(json_files) == 0:
        print("No JSON files found in predictions directory")
        return

    print(f"Found {len(json_files)} prediction JSON files")
    print("=" * 60)

    # Ask for confirmation
    response = input("Do you want to fix all prediction files? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Operation cancelled")
        return

    # Fix all files
    fixed_count = 0
    for json_file in json_files:
        if fix_prediction_file(str(json_file)):
            print(f"✓ Fixed: {json_file.name}")
            fixed_count += 1

    print("=" * 60)
    print(f"Summary: Fixed {fixed_count} out of {len(json_files)} files")

    if fixed_count > 0:
        print("\n✓ Prediction files have been fixed!")
        print("You can now reload the dataset in the application.")


if __name__ == "__main__":
    print("=" * 60)
    print("Prediction JSON File Fixer")
    print("=" * 60)
    print("\nThis script fixes prediction JSON files that use 'name'")
    print("instead of 'class' for the class field.")
    print()
    main()
