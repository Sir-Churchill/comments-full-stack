import bleach
from rest_framework import serializers
from captcha.models import CaptchaStore
from .models import Comment
from .validators import validate_image_file, validate_txt_file

ALLOWED_TAGS = ["a", "code", "i", "strong"]
ALLOWED_ATTRS = {"a": ["href", "title"]}
MAX_TEXT_LENGTH = 10_000


class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source="user.username")
    email = serializers.ReadOnlyField(source="user.email")
    home_page = serializers.ReadOnlyField(source="user.home_page")

    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)

    image = serializers.ImageField(
        required=False,
        allow_null=True,
        validators=[validate_image_file],
    )
    file = serializers.FileField(
        required=False,
        allow_null=True,
        validators=[validate_txt_file],
    )

    children = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "user_name",
            "email",
            "home_page",
            "text",
            "parent",
            "image",
            "file",
            "created_at",
            "captcha_key",
            "captcha_value",
            "children",
        )
        read_only_fields = ("id", "created_at")

    def validate_text(self, value):
        if len(value) > MAX_TEXT_LENGTH:
            raise serializers.ValidationError(
                f"Text must not exceed {MAX_TEXT_LENGTH} characters."
            )

        cleaned = bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True,
        )

        if not cleaned.strip():
            raise serializers.ValidationError(
                "Text content is required and must not be empty after sanitization."
            )

        return cleaned

    def validate_parent(self, value):
        """Prevent cross-linking to a parent that belongs to a deleted subtree."""
        if value is not None and not Comment.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Parent comment does not exist.")
        return value

    def validate_image(self, value):
        if value:
            validate_image_file(value)
        return value

    def validate_file(self, value):
        if value:
            validate_txt_file(value)
        return value

    def validate(self, data):
        key = data.pop("captcha_key", None)
        value = data.pop("captcha_value", None)

        if not key or not value:
            raise serializers.ValidationError(
                {"captcha": "Both captcha_key and captcha_value are required."}
            )

        try:
            captcha = CaptchaStore.objects.get(hashkey=key)
        except CaptchaStore.DoesNotExist:
            raise serializers.ValidationError(
                {"captcha": "Captcha expired or invalid key."}
            )

        import hmac

        if not hmac.compare_digest(captcha.response, value.strip().lower()):
            raise serializers.ValidationError({"captcha": "Invalid captcha value."})

        captcha.delete()

        if data.get("image") and data.get("file"):
            raise serializers.ValidationError(
                "Submit either an image or a text file, not both."
            )

        return data

    def get_children(self, obj):
        depth = self.context.get("depth", 0)
        if depth >= 5:
            return []
        children = obj.get_children()
        if not children:
            return []
        return CommentSerializer(
            children,
            many=True,
            context={**self.context, "depth": depth + 1},
        ).data
