"""
Thumbnail generation module for Image Detection Result Analyzer
Handles generation of thumbnail images using Pillow (PIL)
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image


THUMBNAIL_SIZE = (150, 150)
DEFAULT_THUMBNAIL_DIR = os.path.join('app', 'static', 'thumbnails')


def generate_thumbnail(
    image_path: str,
    output_dir: Optional[str] = None,
    size: Tuple[int, int] = THUMBNAIL_SIZE,
    preserve_aspect_ratio: bool = True
) -> str:
    """
    Generate a thumbnail for an image file

    Args:
        image_path: Path to the source image file
        output_dir: Directory to save the thumbnail (defaults to DEFAULT_THUMBNAIL_DIR)
        size: Thumbnail dimensions as (width, height) tuple (default: 150x150)
        preserve_aspect_ratio: If True, maintain aspect ratio while fitting within size bounds

    Returns:
        str: Path to the generated thumbnail file

    Raises:
        FileNotFoundError: If source image doesn't exist
        ValueError: If source image is not a valid image file
        IOError: If there's an error processing the image
    """
    path = Path(image_path)

    # Validate source file exists
    if not path.exists():
        raise FileNotFoundError(f"Source image not found: {image_path}")

    if not path.is_file():
        raise ValueError(f"Source path is not a file: {image_path}")

    # Set output directory
    if output_dir is None:
        output_dir = DEFAULT_THUMBNAIL_DIR

    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate thumbnail filename (same as source, in thumbnails directory)
    thumbnail_filename = f"thumb_{path.name}"
    thumbnail_path = output_path / thumbnail_filename

    # Skip if thumbnail already exists and is newer than source
    if thumbnail_path.exists():
        if thumbnail_path.stat().st_mtime >= path.stat().st_mtime:
            return str(thumbnail_path)

    # Open and process the image
    try:
        with Image.open(path) as img:
            # Convert RGBA to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Generate thumbnail based on preserve_aspect_ratio setting
            if preserve_aspect_ratio:
                # Create thumbnail with aspect ratio preserved
                # Image will fit within size bounds without distortion
                img.thumbnail(size, Image.Resampling.LANCZOS)
            else:
                # Resize to exact dimensions (may distort image)
                img = img.resize(size, Image.Resampling.LANCZOS)

            # Save the thumbnail
            # Use JPEG format for better compression, PNG for transparency
            if thumbnail_path.suffix.lower() == '.png' or (hasattr(img, 'mode') and img.mode == 'RGBA'):
                img.save(thumbnail_path, 'PNG', optimize=True)
            else:
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

    except Exception as e:
        raise IOError(f"Error generating thumbnail for {image_path}: {e}")

    return str(thumbnail_path)


def generate_thumbnails_from_directory(
    images_dir: str,
    output_dir: Optional[str] = None,
    size: Tuple[int, int] = THUMBNAIL_SIZE,
    preserve_aspect_ratio: bool = True
) -> dict:
    """
    Generate thumbnails for all images in a directory

    Args:
        images_dir: Directory containing source images
        output_dir: Directory to save thumbnails (defaults to DEFAULT_THUMBNAIL_DIR)
        size: Thumbnail dimensions as (width, height) tuple (default: 150x150)
        preserve_aspect_ratio: If True, maintain aspect ratio while fitting within size bounds

    Returns:
        dict: Dictionary with keys:
            - 'success_count': Number of successfully generated thumbnails
            - 'error_count': Number of errors encountered
            - 'thumbnails': List of (source_path, thumbnail_path) tuples
            - 'errors': List of (source_path, error_message) tuples
    """
    path = Path(images_dir)

    if not path.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    if not path.is_dir():
        raise ValueError(f"Source path is not a directory: {images_dir}")

    # Supported image extensions
    supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    results = {
        'success_count': 0,
        'error_count': 0,
        'thumbnails': [],
        'errors': []
    }

    # Process each image in the directory
    for image_file in path.iterdir():
        if not image_file.is_file():
            continue

        if image_file.suffix.lower() not in supported_extensions:
            continue

        try:
            thumbnail_path = generate_thumbnail(
                str(image_file),
                output_dir,
                size,
                preserve_aspect_ratio
            )
            results['thumbnails'].append((str(image_file), thumbnail_path))
            results['success_count'] += 1
        except Exception as e:
            results['errors'].append((str(image_file), str(e)))
            results['error_count'] += 1

    return results


def get_thumbnail_path(image_path: str, thumbnails_dir: Optional[str] = None) -> str:
    """
    Get the expected thumbnail path for an image

    Args:
        image_path: Path to the source image file
        thumbnails_dir: Directory containing thumbnails (defaults to DEFAULT_THUMBNAIL_DIR)

    Returns:
        str: Path to the thumbnail file
    """
    if thumbnails_dir is None:
        thumbnails_dir = DEFAULT_THUMBNAIL_DIR

    path = Path(image_path)
    thumbnail_filename = f"thumb_{path.name}"
    return str(Path(thumbnails_dir) / thumbnail_filename)


def clear_thumbnails_directory(thumbnails_dir: Optional[str] = None) -> int:
    """
    Delete all files in the thumbnails directory

    Args:
        thumbnails_dir: Directory containing thumbnails (defaults to DEFAULT_THUMBNAIL_DIR)

    Returns:
        int: Number of files deleted
    """
    if thumbnails_dir is None:
        thumbnails_dir = DEFAULT_THUMBNAIL_DIR

    path = Path(thumbnails_dir)

    if not path.exists():
        return 0

    if not path.is_dir():
        raise ValueError(f"Thumbnails path is not a directory: {thumbnails_dir}")

    count = 0
    for file in path.iterdir():
        if file.is_file():
            file.unlink()
            count += 1

    return count


if __name__ == "__main__":
    # Test thumbnail generation with a sample image
    import sys

    print("=" * 60)
    print("Thumbnail Generation Test")
    print("=" * 60)

    # Create test directory and sample image
    test_dir = Path('test_dataset')
    test_images_dir = test_dir / 'images'
    test_images_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple test image
    test_image_path = test_images_dir / 'test_image.jpg'
    img = Image.new('RGB', (800, 600), color='blue')
    # Draw some content on the image
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 300, 300], fill='red')
    draw.rectangle([400, 200, 600, 400], fill='green')
    draw.ellipse([100, 400, 300, 500], fill='yellow')
    img.save(test_image_path, 'JPEG', quality=90)

    print(f"\nCreated test image: {test_image_path}")
    print(f"Original dimensions: {img.size}")

    # Test 1: Generate thumbnail with aspect ratio preserved
    print("\n" + "-" * 60)
    print("Test 1: Generate thumbnail with aspect ratio preserved")
    print("-" * 60)

    try:
        thumbnail_path = generate_thumbnail(str(test_image_path))
        print(f"✓ Thumbnail generated successfully")
        print(f"  Thumbnail path: {thumbnail_path}")

        # Verify thumbnail dimensions
        thumb_img = Image.open(thumbnail_path)
        print(f"  Thumbnail dimensions: {thumb_img.size}")

        # Check that thumbnail is within bounds
        assert thumb_img.width <= 150, "Thumbnail width exceeds 150px"
        assert thumb_img.height <= 150, "Thumbnail height exceeds 150px"
        print(f"✓ Thumbnail dimensions verified (within 150x150 bounds)")

        # Calculate expected aspect ratio
        aspect_ratio = 800 / 600
        thumb_aspect_ratio = thumb_img.width / thumb_img.height
        print(f"  Original aspect ratio: {aspect_ratio:.4f}")
        print(f"  Thumbnail aspect ratio: {thumb_aspect_ratio:.4f}")

        # Verify aspect ratio is preserved (allow small floating point error)
        assert abs(aspect_ratio - thumb_aspect_ratio) < 0.01, "Aspect ratio not preserved"
        print(f"✓ Aspect ratio preserved")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Test 2: Generate thumbnail without aspect ratio preservation
    print("\n" + "-" * 60)
    print("Test 2: Generate thumbnail with fixed dimensions")
    print("-" * 60)

    # Clear existing thumbnail to force regeneration
    existing_thumbnail = Path(get_thumbnail_path(str(test_image_path)))
    if existing_thumbnail.exists():
        existing_thumbnail.unlink()
        print(f"Cleared existing thumbnail: {existing_thumbnail}")

    try:
        thumbnail_path_fixed = generate_thumbnail(
            str(test_image_path),
            preserve_aspect_ratio=False
        )
        print(f"✓ Thumbnail generated successfully")
        print(f"  Thumbnail path: {thumbnail_path_fixed}")

        # Verify thumbnail dimensions
        thumb_img_fixed = Image.open(thumbnail_path_fixed)
        print(f"  Thumbnail dimensions: {thumb_img_fixed.size}")

        # Check that thumbnail is exactly 150x150
        assert thumb_img_fixed.width == 150, "Thumbnail width is not 150px"
        assert thumb_img_fixed.height == 150, "Thumbnail height is not 150px"
        print(f"✓ Thumbnail dimensions verified (exactly 150x150)")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Test 3: Batch thumbnail generation from directory
    print("\n" + "-" * 60)
    print("Test 3: Batch thumbnail generation from directory")
    print("-" * 60)

    # Create additional test images
    for i in range(3):
        img_path = test_images_dir / f'test_image_{i}.png'
        img = Image.new('RGB', (640, 480), color=['red', 'green', 'blue'][i])
        img.save(img_path, 'PNG')
        print(f"Created: {img_path}")

    try:
        results = generate_thumbnails_from_directory(str(test_images_dir))
        print(f"\n✓ Batch generation completed")
        print(f"  Success count: {results['success_count']}")
        print(f"  Error count: {results['error_count']}")

        if results['errors']:
            print(f"\n  Errors:")
            for source, error in results['errors']:
                print(f"    {source}: {error}")

        print(f"\n  Generated thumbnails:")
        for source, thumb in results['thumbnails'][:5]:  # Show first 5
            thumb_img = Image.open(thumb)
            print(f"    {Path(source).name} -> {Path(thumb).name} ({thumb_img.size[0]}x{thumb_img.size[1]})")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Test 4: Verify thumbnail path generation
    print("\n" + "-" * 60)
    print("Test 4: Get thumbnail path for an image")
    print("-" * 60)

    try:
        expected_path = get_thumbnail_path(str(test_image_path))
        print(f"✓ Thumbnail path generated")
        print(f"  Image: {test_image_path}")
        print(f"  Expected thumbnail path: {expected_path}")

        # Verify the thumbnail file exists at the expected path
        assert Path(expected_path).exists(), "Thumbnail file does not exist at expected path"
        print(f"✓ Thumbnail file exists at expected path")

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
