from rest_framework.authentication import SessionAuthentication

from rest_framework_simplejwt.authentication import JWTAuthentication

from tigaserver_app.models import TigaUser


class AppUserJWTAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = TigaUser


class NonAppUserSessionAuthentication(SessionAuthentication):
    # Only for User (not TigaUser)
    def authenticate(self, request):
        # Get the session-based user from the underlying HttpRequest object
        user = getattr(request._request, 'user', None)

        if user and isinstance(user, TigaUser):
            return None

        return super().authenticate(request)