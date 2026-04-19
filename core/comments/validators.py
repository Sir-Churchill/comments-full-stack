import os

import magic
from django.core.exceptions import ValidationError

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_TXT_SIZE = 100 * 1024


def validate_image_file(file):
    """Validate image: only JPG, PNG, GIF by extension AND magic bytes."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported image extension: {ext}. Allowed: JPG, PNG, GIF."
        )

    header = file.read(2048)
    file.seek(0)
    mime = magic.from_buffer(header, mime=True)

    if mime not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError(
            f"File content does not match an allowed image type (detected: {mime})."
        )


def validate_txt_file(file):
    """Validate text file: only .txt, max 100 KB, confirmed plain text."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext != ".txt":
        raise ValidationError("Only .txt files are allowed.")

    if file.size > MAX_TXT_SIZE:
        raise ValidationError(
            f"Text file must not exceed 100 KB (got {file.size / 1024:.1f} KB)."
        )

    header = file.read(2048)
    file.seek(0)
    mime = magic.from_buffer(header, mime=True)

    if mime != "text/plain":
        raise ValidationError(f"File content is not plain text (detected: {mime}).")
