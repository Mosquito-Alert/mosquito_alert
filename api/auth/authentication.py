from rest_framework_simplejwt.authentication import JWTAuthentication

from tigaserver_app.models import TigaUser


class AppUserJWTAuthentication(JWTAuthentication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_model = TigaUser
