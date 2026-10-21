#!/usr/bin/env python3
"""Auto-orient images by applying EXIF rotation to pixel data.

Scans all JPEG images under public/images/memorials/ and physically rotates
any that have EXIF orientation != 1. This ensures correct display regardless
of whether the viewer honours EXIF orientation tags.

Run as part of prebuild or manually: python3 scripts/auto-orient-images.py
"""

import glob
import os
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    print("⚠ Pillow not installed — skipping image orientation check")
    sys.exit(0)

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "images", "memorials")

fixed = 0
scanned = 0
errors = 0

for pattern in ("**/*.jpeg", "**/*.jpg", "**/*.JPG", "**/*.JPEG"):
    for f in glob.glob(os.path.join(IMAGES_DIR, pattern), recursive=True):
        scanned += 1
        try:
            img = Image.open(f)
            if not hasattr(img, "_getexif") or img._getexif() is None:
                continue
            orientation = img._getexif().get(274, 1)
            if orientation != 1:
                transposed = ImageOps.exif_transpose(img)
                transposed.save(f, quality=95)
                print(f"  ✓ Fixed orientation {orientation} → 1: {os.path.relpath(f, IMAGES_DIR)}")
                fixed += 1
        except Exception as e:
            errors += 1

if fixed > 0:
    print(f"\nAuto-orient: {fixed} image(s) corrected out of {scanned} scanned.")
elif scanned > 0:
    print(f"Auto-orient: {scanned} images scanned, all correctly oriented.")
