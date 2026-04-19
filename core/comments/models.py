import os
import uuid

from django.conf import settings
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from .validators import validate_image_file, validate_txt_file


def comment_image_path(instance, filename):
    """Store images under comment/images/<user_id>/."""
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"comment/images/{instance.user_id}/{safe_name}"


def comment_file_path(instance, filename):
    """Store txt files under comment/files/<user_id>/."""
    safe_name = f"{uuid.uuid4().hex}.txt"
    return f"comment/files/{instance.user_id}/{safe_name}"


class Comment(MPTTModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = TreeForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )
    text = models.TextField()

    image = models.ImageField(
        upload_to=comment_image_path,
        null=True,
        blank=True,
        validators=[validate_image_file],
    )
    file = models.FileField(
        upload_to=comment_file_path,
        null=True,
        blank=True,
        validators=[validate_txt_file],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class MPTTMeta:
        order_insertion_by = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} at {self.created_at}"
