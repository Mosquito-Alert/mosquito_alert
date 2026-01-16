from abc import ABC, abstractmethod
from typing import Optional
import random
from urllib.parse import urljoin

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import get_random_string

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from rest_framework_simplejwt.tokens import RefreshToken

from tigaserver_app.models import TigaUser

User = get_user_model()


def authenticate_with_token(client, type, token):
    client.credentials(HTTP_AUTHORIZATION=f"{type} {str(token)}")


def grant_permission_to_user(model_class, user, type: Optional[str] = None, codename: Optional[str] = None):
    if type:
        assert type in ["add", "change", "delete", "view"], "type is not a valid option"
        codename=f"{type}_" + model_class._meta.model_name
    elif codename:
        pass
    else:
        raise ValueError("At least one of 'type' or 'codename' must be provided")
    # Get the content type of the model
    content_type = ContentType.objects.get_for_model(model_class)

    # Get or create the permission
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type, codename=codename
    )

    # Assign the permission to the user
    user.user_permissions.add(permission)

    return permission


class AppAPIClient(APIClient):
    def force_login(self, user, backend=None) -> None:
        self.logout()
        return super().force_login(user, backend)

    def _login(self, user, backend=None):
        if isinstance(user, User):
            return super()._login(user, backend)
        elif isinstance(user, TigaUser):
            refresh = RefreshToken.for_user(user)
            authenticate_with_token(
                client=self, type="Bearer", token=refresh.access_token
            )
        else:
            raise NotImplementedError


class _AuthenticableGenericViewMixin(ABC):
    skip_auth_test = False

    @property
    @abstractmethod
    def default_user(self):
        return NotImplementedError

    def _test_auth(self):
        if self.skip_auth_test:
            return

        response = self.client.head(urljoin(self.url, "1/"))
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
            if self.can_auth_with_appuser
            else status.HTTP_401_UNAUTHORIZED,
        )


class AppUserAuthenticableGenericViewMixin(_AuthenticableGenericViewMixin):
    can_auth_with_appuser = True

    @classmethod
    def setUpTestData(cls) -> None:
        cls.app_user = TigaUser.objects.create()
        super().setUpTestData()

    @property
    def default_user(self):
        return self.app_user

    def test_jwt_auth(self):
        self.client.logout()
        self.client.force_login(user=self.app_user)

        self._test_auth()


class TokenAuthenticableGenericViewMixin:
    can_auth_with_token = True

    def test_token_auth(self):
        self.client.logout()
        token = Token.objects.create(user=self.user)
        authenticate_with_token(client=self.client, type="Token", token=token)

        self._test_auth()


class SessionAuthenticableGenericViewMixin:
    can_auth_with_session = True

    def test_session_auth(self):
        self.client.logout()
        self.client.force_login(user=self.user)

        self._test_auth()


class UserAuthenticableGenericViewMixin(
    TokenAuthenticableGenericViewMixin,
    SessionAuthenticableGenericViewMixin,
    _AuthenticableGenericViewMixin,
):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = cls.create_user()
        super().setUpTestData()

    @classmethod
    def create_user(cls):
        return User.objects.create_user(
            username=f"user_{random.randint(1,1000)}",
            password=get_random_string(length=10),
        )

    @property
    def default_user(self):
        return self.user


class GenericViewAPITestCase(
    AppUserAuthenticableGenericViewMixin, UserAuthenticableGenericViewMixin, APITestCase
):
    URL_PREFIX = "/api/v1/"

    client_class = AppAPIClient

    LIST_IS_DISABLED = False
    CREATE_IS_DISABLED = False
    UPDATE_IS_DISABLED = False
    PARTIAL_UPDATE_IS_DISABLED = False
    DELETE_IS_DISABLED = False

    @property
    @abstractmethod
    def ENDPOINT_PATH(self):
        raise NotImplementedError

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

        # Create an app user
        _url = urljoin(base=cls.URL_PREFIX, url=cls.ENDPOINT_PATH)
        if not _url.endswith("/"):
            _url += "/"

        cls.url = _url

    def _callSetUp(self) -> None:
        self.login_default_user()
        super()._callSetUp()

    def login_default_user(self):
        self.client.force_login(user=self.app_user)

    # LIST
    def test_list_is_disabled(self):
        self.login_default_user()

        # Attempt to create a campaign, it should return Method Not Allowed (405)
        response = self.client.get(self.url, format="json")
        if self.LIST_IS_DISABLED:
            self.assertIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )
        else:
            self.assertNotIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )

    # CREATE
    def test_create_is_disabled(self):
        self.login_default_user()

        # Attempt to create a campaign, it should return Method Not Allowed (405)
        response = self.client.post(self.url, {}, format="json")
        if self.CREATE_IS_DISABLED:
            self.assertIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )
        else:
            self.assertNotIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )

    # UPDATE
    def test_update_is_disabled(self):
        self.login_default_user()

        # Attempt to update a campaign, it should return Method Not Allowed (405)
        response = self.client.put(urljoin(self.url, "1/"), {}, format="json")
        if self.UPDATE_IS_DISABLED:
            self.assertIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )
        else:
            self.assertNotIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )

    # PARTIAL UPDATE
    def test_partial_update_is_disabled(self):
        self.login_default_user()

        # Attempt to partially update a campaign, it should return Method Not Allowed (405)
        response = self.client.patch(urljoin(self.url, "1/"), {}, format="json")
        if self.PARTIAL_UPDATE_IS_DISABLED:
            self.assertIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )
        else:
            self.assertNotIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )

    # DELETE
    def test_delete_is_disabled(self):
        self.login_default_user()

        # Attempt to delete a campaign, it should return Method Not Allowed (405)
        response = self.client.delete(urljoin(self.url, "1/"))
        if self.DELETE_IS_DISABLED:
            self.assertIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )
        else:
            self.assertNotIn(
                response.status_code,
                (status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_404_NOT_FOUND),
            )
