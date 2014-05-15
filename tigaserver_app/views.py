from rest_framework import viewsets, views
from serializers import UserSerializer, ReportSerializer, MissionSerializer, PhotoSerializer
from models import TigaUser, Report, Mission, Photo
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import mixins
from rest_framework.permissions import DjangoModelPermissions
from custom_permissions import *
from django.views.decorators.http import require_http_methods
from rest_framework import generics



class ReadOnlyModelViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides `retrieve`, andlist` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


class WriteOnlyModelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    A viewset that provides`create` action.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


@api_view(['POST'])
def upload_form(request):
    """
    A function for uploading photos and related database entries as multipart form data.

    The photo file must be named 'photo', and its associated report's version_UUID must be named 'report'
    """
    if request.method == 'POST':
        this_report = Report.objects.get(version_UUID=request.DATA['report'])
        instance = Photo(photo=request.FILES['photo'], report=this_report)
        instance.save()
        return Response('uploaded')


class UserViewSet(WriteOnlyModelViewSet):
    """
    API endpoint that allows new users to be posted.
    """
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer


class ReportViewSet(WriteOnlyModelViewSet):
    """
    API endpoint that allows new reports or new report versions to be posted.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer


class MissionViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows missions to be downloaded.
    """
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer


class PhotoViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows photos to be uploaded a multipart form data.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
