import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token: str):
    """
    Validate a JWT access token and return the corresponding User,
    or AnonymousUser if the token is invalid/expired.
    Uses the same logic as DRF SimpleJWT's JWTAuthentication.
    """
    try:
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

        validated = AccessToken(token)
        user_id = validated['user_id']
        return User.objects.get(pk=user_id)
    except Exception:
        return AnonymousUser()


class CommentConsumer(AsyncWebsocketConsumer):
    GROUP = 'comments'

    async def connect(self):
        # Accept immediately so the client can send the auth message.
        # The connection is not yet considered authenticated.
        self.user = AnonymousUser()
        self.authenticated = False

        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.accept()

        # Give the client 5 seconds to send {"type":"auth","token":"..."}
        # After that any write operations are refused.
        import asyncio
        self._auth_task = asyncio.get_event_loop().call_later(
            5, self._auth_timeout
        )

    def _auth_timeout(self):
        """Called if no auth message received within 5 s. Mark as guest-only."""
        self.authenticated = False

    async def disconnect(self, code):
        if hasattr(self, '_auth_task'):
            self._auth_task.cancel()
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        msg_type = data.get('type')

        # ── Authentication handshake ─────────────────────────────────────────
        if msg_type == 'auth':
            token = data.get('token', '')
            if token:
                self.user = await get_user_from_token(token)
                self.authenticated = not isinstance(self.user, AnonymousUser)

            await self.send(text_data=json.dumps({
                'type': 'auth.result',
                'authenticated': self.authenticated,
                'username': self.user.username if self.authenticated else None,
            }))
            return

        if not self.authenticated:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Authentication required.',
            }))

    async def comment_new(self, event):
        await self.send(text_data=json.dumps({
            'type': 'comment.new',
            'comment': event['comment'],
        }))

    async def comment_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'comment.deleted',
            'id': event['id'],
        }))