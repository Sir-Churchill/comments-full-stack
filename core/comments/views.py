from asgiref.sync import async_to_sync
from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from channels.layers import get_channel_layer
from django.db.models import Prefetch
from rest_framework import viewsets, filters, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comment
from .serializers import CommentSerializer
from .tasks import process_comment_image


class CaptchaView(APIView):
    permission_classes = []

    def get(self, request):
        new_key = CaptchaStore.pick()
        image_url = request.build_absolute_uri(captcha_image_url(new_key))

        return Response(
            {
                "key": new_key,
                "image_url": image_url,
            }
        )


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["user__username", "user__email", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Оптимизируем запросы через select_related и prefetch_related,
        чтобы избежать проблемы N+1 при загрузке дерева.
        """
        queryset = Comment.objects.select_related("user").prefetch_related(
            Prefetch("children", queryset=Comment.objects.select_related("user"))
        )

        if self.action == "list":
            return queryset.filter(parent=None)

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)

        if instance.image:
            process_comment_image.delay(instance.image.path)

        channel_layer = get_channel_layer()
        comment_data = CommentSerializer(instance, context={'request': self.request}).data
        async_to_sync(channel_layer.group_send)(
            'comments',
            {
                'type': 'comment.new',
                'comment': comment_data,
            }
        )

    def get_permissions(self):
        """
        Анонимы могут только смотреть, писать могут только авторизованные (JWT).
        """
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
