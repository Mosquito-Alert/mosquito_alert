from drf_spectacular.utils import extend_schema
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework import status


@extend_schema(
    responses={204: None},  # No content
    description="Simple ping endpoint to check API connectivity",
)
@api_view(["GET"])
@authentication_classes([])  # no auth
@permission_classes([])  # no permissions
def ping(request):
    return Response(status=status.HTTP_204_NO_CONTENT)
