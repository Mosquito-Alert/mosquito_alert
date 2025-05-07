from contextlib import contextmanager

from django.contrib.auth import get_user_model

from rest_framework.authentication import SessionAuthentication

from rest_framework_simplejwt.authentication import JWTAuthentication

from tigaserver_app.models import TigaUser

from .tokens import Token


class AppUserJWTAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.user_model

    @contextmanager
    def set_user_model(self, validated_token):
        user_type = validated_token[Token.USER_TYPE_CLAIM]
        if user_type == Token.USER_TYPE_MOBILE_ONLY:
            self.user_model = TigaUser
        elif user_type == Token.USER_TYPE_REGULAR:
            self.user_model = get_user_model()
        else:
            raise ValueError("Invalid user type")

        try:
            yield
        finally:
            del self.user_model

    def get_user(self, validated_token):
        with self.set_user_model(validated_token):
            return super().get_user(validated_token)


class NonAppUserSessionAuthentication(SessionAuthentication):
    # Only for User (not TigaUser)
    def authenticate(self, request):
        # Get the session-based user from the underlying HttpRequest object
        user = getattr(request._request, 'user', None)

        if user and isinstance(user, TigaUser):
            return None

        return super().authenticate(request)