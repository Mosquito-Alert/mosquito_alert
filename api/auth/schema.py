from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme


class AppUserJWTAuthentication(SimpleJWTScheme):
    target_class = "api.auth.authentication.AppUserJWTAuthentication"
