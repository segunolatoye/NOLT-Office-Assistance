#!/usr/bin/env python3
"""
Simple script to generate a basic favicon for PDF Image Toolkit.
Run this to create a favicon.ico in the project root.
"""

from PIL import Image, ImageDraw
from pathlib import Path


def create_favicon(output_path: str | Path = "favicon.ico", size: int = 256) -> None:
    """
    Create a simple PDF/Document themed favicon.
    
    Args:
        output_path: Where to save the favicon
        size: Icon size in pixels (will be converted to standard favicon size)
    """
    # Create a new image with a light background
    img = Image.new("RGB", (size, size), color=(245, 246, 248))
    draw = ImageDraw.Draw(img)
    
    # Draw a document/PDF icon
    padding = size // 8
    rect_left = padding
    rect_top = padding
    rect_right = size - padding
    rect_bottom = size - 3 * padding
    
    # Document outline (dark blue)
    draw.rectangle(
        [(rect_left, rect_top), (rect_right, rect_bottom)],
        outline=(41, 128, 185),
        width=max(1, size // 32)
    )
    
    # Lines on document (red accent)
    line_spacing = (rect_bottom - rect_top) // 4
    line_y = rect_top + line_spacing
    for _ in range(2):
        draw.line(
            [(rect_left + padding // 2, line_y), (rect_right - padding // 2, line_y)],
            fill=(231, 76, 60),
            width=max(1, size // 64)
        )
        line_y += line_spacing
    
    # Convert to standard favicon size (32x32 is most compatible)
    favicon_size = 32
    img_resized = img.resize((favicon_size, favicon_size), Image.Resampling.LANCZOS)
    
    # Save as ICO
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img_resized.save(output_path, format="ICO")
    
    print(f"✓ Favicon created: {output_path}")
    print(f"  Size: {favicon_size}x{favicon_size} pixels")
    print(f"  Format: ICO")


if __name__ == "__main__":
    create_favicon()
