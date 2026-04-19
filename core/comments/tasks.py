import os
from celery import shared_task
from PIL import Image
import magic
from django.core.management import call_command

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/gif"}


@shared_task
def process_comment_image(image_path):
    """
    Re-validates file type by magic bytes BEFORE processing,
    then proportionally resizes to 320x240.
    """
    if not os.path.exists(image_path):
        return "File not found"

    with open(image_path, "rb") as f:
        header = f.read(2048)
    mime = magic.from_buffer(header, mime=True)
    if mime not in ALLOWED_IMAGE_MIME_TYPES:
        os.remove(image_path)
        return f"Rejected: unexpected MIME type '{mime}', file deleted."

    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        os.remove(image_path)
        return f"Rejected: image verification failed ({e}), file deleted."

    try:
        with Image.open(image_path) as img:
            img.thumbnail((320, 240))

            fmt = Image.open(image_path).format
            img.save(image_path, format=fmt)
        return f"Success: {image_path} resized"
    except Exception as e:
        return f"Error: {str(e)}"


@shared_task
def clear_expired_captchas():
    call_command("captcha_clean")
