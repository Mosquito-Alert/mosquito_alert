
from rest_framework import status, generics
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema_view, extend_schema

from ..viewsets import GenericMobileOnlyViewSet

from .serializers import GuestRegistrationSerializer, PasswordChangeSerializer


@extend_schema_view(
    post=extend_schema(
        operation_id='signup_guest',
    )
)
class GuestRegisterView(generics.CreateAPIView):
    authentication_classes = ()
    serializer_class = GuestRegistrationSerializer
    permission_classes = ()

class PasswordChangeView(generics.CreateAPIView):
    authentication_classes = GenericMobileOnlyViewSet.authentication_classes
    permission_classes = GenericMobileOnlyViewSet.permission_classes
    serializer_class = PasswordChangeSerializer

    @extend_schema(
        operation_id='change_password',
        responses={
            200: PasswordChangeSerializer,
        }
    )
    def post(self, request, format=None):
        user = request.user
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()

            content = {'success': 'Password changed.'}
            return Response(content, status=status.HTTP_200_OK)

        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
