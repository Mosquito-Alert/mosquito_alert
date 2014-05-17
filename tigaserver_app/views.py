from rest_framework import viewsets
from serializers import UserSerializer, ReportSerializer, MissionSerializer, PhotoSerializer, FixSerializer, \
    ConfigurationSerializer, ReportResponseSerializer
from models import TigaUser, Mission, MissionTrigger, MissionItem, Report, ReportResponse,  Photo, \
    Fix, Configuration
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import mixins


class ReadOnlyModelViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
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


class ReadWriteOnlyModelViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    A viewset that provides`create` action.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass


@api_view(['POST'])
def upload_form(request):
    """
    A function for uploading photos and related database entries as multipart form data. The photo file must be named 'photo', and its associated report's version_UUID must be named 'report'
    """
    if request.method == 'POST':
        this_report = Report.objects.get(version_UUID=request.DATA['report'])
        instance = Photo(photo=request.FILES['photo'], report=this_report)
        instance.save()
        return Response('uploaded')


# For production version, substitute WriteOnlyModelViewSet
class UserViewSet(ReadWriteOnlyModelViewSet):
    """
    API endpoint that allows new users to be posted.
    """
    queryset = TigaUser.objects.all()
    serializer_class = UserSerializer


# For production version, substitute WriteOnlyModelViewSet
class ReportViewSet(ReadWriteOnlyModelViewSet):
    """
    API endpoint that allows new reports or new report versions to be posted.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer


class MissionViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows users to download missions created by MoveLab.
    """
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer


# For production version, substitute WriteOnlyModelViewSet
class PhotoViewSet(ReadWriteOnlyModelViewSet):
    """
    API endpoint that allows photos to be uploaded as multipart form data.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer


# For production version, substitute WriteOnlyModelViewSet
class FixViewSet(ReadWriteOnlyModelViewSet):
    """
    API endpoint that allows location fixes to be posted.
    """
    queryset = Fix.objects.all()
    serializer_class = FixSerializer


class ConfigurationViewSet(ReadOnlyModelViewSet):
    """
API endpoint that allows users to download app configuration created by Movelab.

* id: Auto-incremented primary key record ID.
* samples_per_day: Number of randomly-timed location samples to take per day.
* creation_time: Date and time when this configuration was created by MoveLab. Automatically generated when
record is saved.
    """
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
