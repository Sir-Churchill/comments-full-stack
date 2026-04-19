from unittest.mock import patch

from captcha.models import CaptchaStore
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Comment
from .serializers import CommentSerializer
from .validators import validate_image_file, validate_txt_file

User = get_user_model()


def make_user(username="alice", email="alice@example.com", password="pass1234!"):
    return User.objects.create_user(username=username, email=email, password=password)


def auth_client(user):
    """Return an APIClient authenticated via JWT for *user*."""
    from rest_framework.test import APIClient

    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


def fresh_captcha():
    """Create a CaptchaStore entry and return (key, plaintext_response)."""
    key = CaptchaStore.pick()
    captcha = CaptchaStore.objects.get(hashkey=key)
    return key, captcha.response


def minimal_gif():
    return (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
        b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
        b"\x00\x00\x02\x02D\x01\x00;"
    )


def minimal_png():
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde"
        b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def uploaded_gif(name="test.gif"):
    return SimpleUploadedFile(name, minimal_gif(), content_type="image/gif")


def uploaded_png(name="test.png"):
    return SimpleUploadedFile(name, minimal_png(), content_type="image/png")


def uploaded_txt(content=b"Hello world", name="test.txt"):
    return SimpleUploadedFile(name, content, content_type="text/plain")


class ValidateImageFileTests(TestCase):

    def test_valid_gif_passes(self):
        f = uploaded_gif()
        with patch("comments.validators.magic.from_buffer", return_value="image/gif"):
            validate_image_file(f)

    def test_valid_png_passes(self):
        f = uploaded_png()
        with patch("comments.validators.magic.from_buffer", return_value="image/png"):
            validate_image_file(f)

    def test_wrong_extension_rejected(self):
        f = SimpleUploadedFile("photo.bmp", b"BM...", content_type="image/bmp")
        with self.assertRaises(ValidationError) as ctx:
            validate_image_file(f)
        self.assertIn("Unsupported image extension", str(ctx.exception))

    def test_mime_mismatch_rejected(self):
        f = SimpleUploadedFile("photo.jpg", b"%PDF-1.4", content_type="image/jpeg")
        with patch(
            "comments.validators.magic.from_buffer", return_value="application/pdf"
        ):
            with self.assertRaises(ValidationError) as ctx:
                validate_image_file(f)
        self.assertIn("does not match an allowed image type", str(ctx.exception))

    def test_file_pointer_reset_after_validation(self):
        f = uploaded_gif()
        with patch("comments.validators.magic.from_buffer", return_value="image/gif"):
            validate_image_file(f)
        self.assertEqual(f.tell(), 0)


class ValidateTxtFileTests(TestCase):

    def test_valid_txt_passes(self):
        f = uploaded_txt()
        with patch("comments.validators.magic.from_buffer", return_value="text/plain"):
            validate_txt_file(f)

    def test_wrong_extension_rejected(self):
        f = SimpleUploadedFile("doc.pdf", b"content", content_type="text/plain")
        with self.assertRaises(ValidationError) as ctx:
            validate_txt_file(f)
        self.assertIn("Only .txt files are allowed", str(ctx.exception))

    def test_oversized_file_rejected(self):
        big = SimpleUploadedFile(
            "big.txt", b"x" * (100 * 1024 + 1), content_type="text/plain"
        )
        with self.assertRaises(ValidationError) as ctx:
            validate_txt_file(big)
        self.assertIn("must not exceed 100 KB", str(ctx.exception))

    def test_exactly_100kb_passes(self):
        f = SimpleUploadedFile(
            "edge.txt", b"x" * (100 * 1024), content_type="text/plain"
        )
        with patch("comments.validators.magic.from_buffer", return_value="text/plain"):
            validate_txt_file(f)

    def test_non_plain_text_mime_rejected(self):
        f = uploaded_txt(name="sneaky.txt")
        with patch(
            "comments.validators.magic.from_buffer",
            return_value="application/octet-stream",
        ):
            with self.assertRaises(ValidationError) as ctx:
                validate_txt_file(f)
        self.assertIn("not plain text", str(ctx.exception))

    def test_file_pointer_reset_after_validation(self):
        f = uploaded_txt()
        with patch("comments.validators.magic.from_buffer", return_value="text/plain"):
            validate_txt_file(f)
        self.assertEqual(f.tell(), 0)


class CommentModelTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_root_comment(self):
        comment = Comment.objects.create(user=self.user, text="Hello!")
        self.assertIsNotNone(comment.pk)
        self.assertIsNone(comment.parent)
        self.assertTrue(comment.is_root_node())

    def test_create_child_comment(self):
        root = Comment.objects.create(user=self.user, text="Root")
        child = Comment.objects.create(user=self.user, text="Child", parent=root)
        self.assertEqual(child.parent, root)
        self.assertIn(child, root.get_children())

    def test_str_representation(self):
        comment = Comment.objects.create(user=self.user, text="Hi")
        self.assertIn(self.user.username, str(comment))

    def test_cascade_delete_removes_children(self):
        root = Comment.objects.create(user=self.user, text="Root")
        Comment.objects.create(user=self.user, text="Child", parent=root)
        root.delete()
        self.assertEqual(Comment.objects.count(), 0)

    def test_created_at_is_set_automatically(self):
        comment = Comment.objects.create(user=self.user, text="Auto time")
        self.assertIsNotNone(comment.created_at)

    def test_image_and_file_are_optional(self):
        comment = Comment.objects.create(user=self.user, text="No attachments")
        self.assertFalse(comment.image)
        self.assertFalse(comment.file)



class CommentSerializerTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def _base_data(self, text="<strong>Hello</strong>", parent=None, extra=None):
        key, response = fresh_captcha()
        data = {
            "text": text,
            "captcha_key": key,
            "captcha_value": response,
        }
        if parent is not None:
            data["parent"] = parent.pk
        if extra:
            data.update(extra)
        return data

    def test_valid_data_is_valid(self):
        serializer = CommentSerializer(data=self._base_data())
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_text_is_sanitized(self):
        data = self._base_data(text='<script>alert("xss")</script><strong>ok</strong>')
        serializer = CommentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn("<script>", serializer.validated_data["text"])
        self.assertIn("<strong>ok</strong>", serializer.validated_data["text"])

    def test_allowed_html_tags_preserved(self):
        html = '<a href="http://example.com">link</a> <code>x</code> <i>i</i>'
        serializer = CommentSerializer(data=self._base_data(text=html))
        self.assertTrue(serializer.is_valid(), serializer.errors)
        cleaned = serializer.validated_data["text"]
        self.assertIn("<a ", cleaned)
        self.assertIn("<code>", cleaned)

    def test_text_too_long_is_rejected(self):
        serializer = CommentSerializer(data=self._base_data(text="a" * 10_001))
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_empty_text_after_sanitization_rejected(self):
        serializer = CommentSerializer(data=self._base_data(text="<script></script>"))
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_missing_captcha_key_rejected(self):
        _, response = fresh_captcha()
        serializer = CommentSerializer(data={"text": "hi", "captcha_value": response})
        self.assertFalse(serializer.is_valid())

    def test_wrong_captcha_value_rejected(self):
        key, _ = fresh_captcha()
        serializer = CommentSerializer(
            data={"text": "hi", "captcha_key": key, "captcha_value": "wrong"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("captcha", str(serializer.errors).lower())

    def test_expired_captcha_key_rejected(self):
        serializer = CommentSerializer(
            data={"text": "hi", "captcha_key": "nonexistent", "captcha_value": "abc"}
        )
        self.assertFalse(serializer.is_valid())

    def test_captcha_deleted_after_successful_validation(self):
        key, response = fresh_captcha()
        serializer = CommentSerializer(
            data={"text": "hello", "captcha_key": key, "captcha_value": response}
        )
        serializer.is_valid()
        self.assertFalse(CaptchaStore.objects.filter(hashkey=key).exists())

    def test_both_image_and_file_rejected(self):
        gif = uploaded_gif()
        txt = uploaded_txt()
        data = self._base_data(extra={"image": gif, "file": txt})
        serializer = CommentSerializer(data=data)

        def magic_side_effect(buffer, mime=True):
            if b"GIF" in buffer:
                return "image/gif"
            return "text/plain"

        with patch(
            "comments.validators.magic.from_buffer", side_effect=magic_side_effect
        ):
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_children_field_respects_depth_limit(self):
        root = Comment.objects.create(user=self.user, text="root")
        Comment.objects.create(user=self.user, text="child", parent=root)
        shallow = CommentSerializer(root, context={"depth": 4})
        deep = CommentSerializer(root, context={"depth": 5})
        self.assertNotEqual(shallow.data["children"], [])
        self.assertEqual(deep.data["children"], [])

    def test_read_only_user_fields_present(self):
        comment = Comment.objects.create(user=self.user, text="hello")
        data = CommentSerializer(comment).data
        self.assertEqual(data["user_name"], self.user.username)
        self.assertEqual(data["email"], self.user.email)


class CaptchaViewTests(APITestCase):

    def test_get_returns_key_and_image_url(self):
        response = self.client.get(reverse("captcha"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("key", response.data)
        self.assertIn("image_url", response.data)

    def test_each_request_returns_unique_key(self):
        url = reverse("captcha")
        r1 = self.client.get(url)
        r2 = self.client.get(url)
        self.assertNotEqual(r1.data["key"], r2.data["key"])


class CommentListViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.url = reverse("comments-list")

    def test_anonymous_can_list_comments(self):
        Comment.objects.create(user=self.user, text="Public comment")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_only_root_comments(self):
        root = Comment.objects.create(user=self.user, text="Root")
        child = Comment.objects.create(user=self.user, text="Child", parent=root)
        response = self.client.get(self.url)
        ids = [c["id"] for c in response.data["results"]]
        self.assertIn(root.pk, ids)
        self.assertNotIn(child.pk, ids)

    def test_ordering_by_created_at_desc_by_default(self):
        c1 = Comment.objects.create(user=self.user, text="First")
        c2 = Comment.objects.create(user=self.user, text="Second")
        response = self.client.get(self.url)
        ids = [c["id"] for c in response.data["results"]]
        self.assertEqual(ids[0], c2.pk)

    def test_pagination_defaults_to_25(self):
        for i in range(30):
            Comment.objects.create(user=self.user, text=f"comment {i}")
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["results"]), 25)

    def test_ordering_by_username(self):
        u1 = make_user("zara", "zara@example.com")
        u2 = make_user("anna", "anna@example.com")
        Comment.objects.create(user=u1, text="z comment")
        Comment.objects.create(user=u2, text="a comment")
        response = self.client.get(self.url + "?ordering=user__username")
        usernames = [c["user_name"] for c in response.data["results"]]
        self.assertEqual(usernames, sorted(usernames))


class CommentCreateViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.url = reverse("comments-list")

    def _post(self, client, data):
        return client.post(self.url, data, format="multipart")

    def test_anonymous_cannot_create(self):
        key, val = fresh_captcha()
        response = self.client.post(
            self.url, {"text": "hi", "captcha_key": key, "captcha_value": val}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_create(self):
        client = auth_client(self.user)
        key, val = fresh_captcha()
        response = self._post(
            client, {"text": "A new comment", "captcha_key": key, "captcha_value": val}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(user=self.user).exists())

    def test_comment_owner_is_request_user(self):
        client = auth_client(self.user)
        key, val = fresh_captcha()
        self._post(client, {"text": "mine", "captcha_key": key, "captcha_value": val})
        comment = Comment.objects.get(user=self.user)
        self.assertEqual(comment.user, self.user)

    def test_create_reply_to_existing_comment(self):
        root = Comment.objects.create(user=self.user, text="root")
        client = auth_client(self.user)
        key, val = fresh_captcha()
        response = self._post(
            client,
            {
                "text": "reply",
                "captcha_key": key,
                "captcha_value": val,
                "parent": root.pk,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        child = Comment.objects.get(text="reply")
        self.assertEqual(child.parent, root)

    def test_invalid_parent_rejected(self):
        client = auth_client(self.user)
        key, val = fresh_captcha()
        response = self._post(
            client,
            {
                "text": "reply",
                "captcha_key": key,
                "captcha_value": val,
                "parent": 99999,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_image_triggers_celery_task(self):
        client = auth_client(self.user)
        key, val = fresh_captcha()
        gif = uploaded_gif()
        with patch(
            "comments.validators.magic.from_buffer", return_value="image/gif"
        ), patch("comments.tasks.process_comment_image.delay") as mock_task:
            response = self._post(
                client,
                {
                    "text": "with image",
                    "captcha_key": key,
                    "captcha_value": val,
                    "image": gif,
                },
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_task.assert_called_once()

    def test_create_without_image_does_not_trigger_celery(self):
        client = auth_client(self.user)
        key, val = fresh_captcha()
        with patch("comments.tasks.process_comment_image.delay") as mock_task:
            self._post(
                client, {"text": "no image", "captcha_key": key, "captcha_value": val}
            )
        mock_task.assert_not_called()

    def test_xss_in_text_is_stripped_on_create(self):
        client = auth_client(self.user)
        key, val = fresh_captcha()
        response = self._post(
            client,
            {
                "text": "<script>alert(1)</script><strong>safe</strong>",
                "captcha_key": key,
                "captcha_value": val,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(user=self.user)
        self.assertNotIn("<script>", comment.text)
        self.assertIn("<strong>", comment.text)


class CommentRetrieveViewTests(APITestCase):

    def setUp(self):
        self.user = make_user()

    def test_anonymous_can_retrieve(self):
        comment = Comment.objects.create(user=self.user, text="visible")
        response = self.client.get(reverse("comments-detail", args=[comment.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], comment.pk)

    def test_children_nested_in_retrieve(self):
        root = Comment.objects.create(user=self.user, text="root")
        child = Comment.objects.create(user=self.user, text="child", parent=root)
        response = self.client.get(reverse("comments-detail", args=[root.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        children_ids = [c["id"] for c in response.data["children"]]
        self.assertIn(child.pk, children_ids)


class CommentPermissionTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.comment = Comment.objects.create(user=self.user, text="original")
        self.url = reverse("comments-detail", args=[self.comment.pk])

    def test_unauthenticated_cannot_update(self):
        response = self.client.patch(self.url, {"text": "hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_cannot_delete(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_delete_own_comment(self):
        client = auth_client(self.user)
        response = client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=self.comment.pk).exists())
