from datetime import timedelta
import pytest
import time_machine

from django.conf import settings
from django.http import HttpResponse

from rest_framework import permissions
from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.viewsets import GenericViewSet as DRFGenericViewSet

from rest_framework_simplejwt.settings import api_settings

from api.auth.authentication import JWTAuthentication
from api.viewsets import GenericViewSet, GenericMobileOnlyViewSet, GenericNoMobileViewSet
from api.tests.clients import AppAPIClient


factory = APIRequestFactory()

class MockViewSet(DRFGenericViewSet):
    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse(status=201)

class BaseTestGenericViewSet:
    @classmethod
    def create_mock_view(cls, actions: dict):
        return cls.MockGenericViewSet.as_view(actions=actions)

class AppUserJWTAuthenticationTestMixin:
    def test_unauth_access_must_return_401(self):
        view = self.create_mock_view(actions={'get': 'get'})

        request = factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        # Should be the one from JWT
        assert response.headers['WWW-Authenticate'] == JWTAuthentication().authenticate_header(request)

    def test_expired_jwt_accesss_token_must_return_401(self, app_user):
        view = self.create_mock_view(actions={'get': 'get'})

        with time_machine.travel("2024-01-01 00:00:00", tick=False) as traveller:
            app_api_client = AppAPIClient()
            app_api_client.force_login(user=app_user)

            request = factory.get('/', **app_api_client._credentials)
            response = view(request)
            assert response.status_code == status.HTTP_200_OK

            traveller.shift(api_settings.ACCESS_TOKEN_LIFETIME + timedelta(seconds=1))

            response = view(request)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TokenAuthenticationTestMixin:
    def test_auth_with_token_must_return_200(self, token_user):
        view = self.create_mock_view(actions={'get': 'get'})

        request = factory.get('/', HTTP_AUTHORIZATION=f"Token {str(token_user)}")
        response = view(request)
        assert response.status_code == status.HTTP_200_OK


class NonAppUserSessionAuthenticationTestMixin:
    @pytest.mark.parametrize(
        "method, include_csrf, expected_status_code",
        [
            ('GET', True, status.HTTP_200_OK),
            ('GET', False, status.HTTP_200_OK),
            ('POST', True, status.HTTP_201_CREATED),
            ('POST', False, status.HTTP_403_FORBIDDEN),
        ]
    )
    def test_session_auth_csrf(self, non_app_api_client, user, method, include_csrf, expected_status_code):
        view = self.create_mock_view(actions={method: method.lower()})

        csrf_factory = APIRequestFactory(enforce_csrf_checks=True)
        csrf_factory.cookies = non_app_api_client.cookies

        data = {}
        if include_csrf:
            # Set the csrf_token cookie so that CsrfViewMiddleware._get_token() works
            from django.middleware.csrf import (
                _get_new_csrf_string, _mask_cipher_secret
            )
            token = _mask_cipher_secret(_get_new_csrf_string())
            csrf_factory.cookies[settings.CSRF_COOKIE_NAME] = token
            data['csrfmiddlewaretoken'] = token

        data, content_type = csrf_factory._encode_data(data)
        request = csrf_factory.generic(method, '/', data, content_type)
        request.user = user
        response = view(request)
        assert response.status_code == expected_status_code


@pytest.mark.django_db
class TestGenericViewSet(AppUserJWTAuthenticationTestMixin, TokenAuthenticationTestMixin, NonAppUserSessionAuthenticationTestMixin, BaseTestGenericViewSet):
    class MockGenericViewSet(GenericViewSet, MockViewSet):
        permission_classes = (permissions.IsAuthenticated,)

@pytest.mark.django_db
class TestGenericMobileOnlyViewSet(AppUserJWTAuthenticationTestMixin, BaseTestGenericViewSet):
    class MockGenericViewSet(GenericMobileOnlyViewSet, MockViewSet):
        permission_classes = (permissions.IsAuthenticated,)

@pytest.mark.django_db
class TestGenericNoMobileViewSet(NonAppUserSessionAuthenticationTestMixin, TokenAuthenticationTestMixin, BaseTestGenericViewSet):
    class MockGenericViewSet(GenericNoMobileViewSet, MockViewSet):
        permission_classes = (permissions.IsAuthenticated,)