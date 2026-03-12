import logging
from typing import Callable

from django.http.request import HttpRequest
from django.http.response import HttpResponse

from .models import TigaUser

logger = logging.getLogger(__name__)

APP_USER_QUERYSTRING_KEY = "app_uuid"
APP_USER_SESSION_KEY = "app_user:session"

class AppUserRequestMiddleware:
    """Extract App User token from incoming request."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.app_user = None
        request.user.is_app_user = False
        app_user_uuid = request.GET.get(APP_USER_QUERYSTRING_KEY)
        if not app_user_uuid:
            return self.get_response(request)

        try:
            app_user = TigaUser.objects.get(pk=app_user_uuid)
        except TigaUser.DoesNotExist:
            logger.debug("app_user pass does not exist: %s", app_user_uuid)
            return self.get_response(request)
        else:
            request.app_user = app_user
            request.user.is_app_user = True
        return self.get_response(request)


class AppUserSessionMiddleware:
    """Extract app user info from session and update request user."""

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Update request.user if any app_user vars are found in session.

        This middleware should run after the AppUserRequestMiddleware. If
        a request comes in without a app_user token in the querystring, we
        need to check the request.session to see if any app_user data was
        stashed previously.

        The first time this middleware runs after a new session is created
        this will push the `request.app_user` info into the session.
        Subsequent requests will then get the data out of the session.

        """
        # This will only be true directly after AppUserRequestMiddleware
        # has set the values. All subsequent requests in the session will
        # start with is_app_user=False and pick up the app_user info from
        # the session.
        if request.app_user:
            request.session[APP_USER_SESSION_KEY] = request.app_user.pk
            return self.get_response(request)

        # We don't have a app_user object, but there may be one in the session
        if not (app_user_uuid := request.session.get(APP_USER_SESSION_KEY, "")):
            return self.get_response(request)

        try:
            app_user = TigaUser.objects.get(
                uuid=app_user_uuid,
            )
        except TigaUser.DoesNotExist:
            request.session.pop(APP_USER_SESSION_KEY, "")
            return self.get_response(request)
        else:
            request.app_user = app_user
            request.user.is_app_user = True

        return self.get_response(request)