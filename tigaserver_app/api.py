from tastypie import fields
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie.resources import ModelResource
from tigaserver_app.models import Report, TigaUser, Mission, Photo


class UserResource(ModelResource):
    class Meta:
        queryset = TigaUser.objects.all()
        resource_name = 'user'
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        list_allowed_methods = ['post']
        detail_allowed_methods = ['post']


class ReportResource(ModelResource):
    user = fields.ForeignKey(UserResource, 'user')

    class Meta:
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        queryset = Report.objects.all()
        resource_name = 'report'
        list_allowed_methods = ['post']
        detail_allowed_methods = ['post']


class MissionResource(ModelResource):
    class Meta:
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        queryset = Mission.objects.all()
        resource_name = 'mission'
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

""""
class MultipartResource(object):
    def deserialize(self, request, data, format=None):
        if not format:
            format = request.META.get('CONTENT_TYPE', 'application/json')
        if format == 'application/x-www-form-urlencoded':
            return request.POST
        if format.startswith('multipart'):
            data = request.POST.copy()
            data.update(request.FILES)
            return data
        return super(MultipartResource, self).deserialize(request, data, format)


class PhotoResource(ModelResource):
    report = fields.ForeignKey(ReportResource, 'report')

    class Meta:
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        queryset = Photo.objects.all()
        resource_name = 'photo'
        list_allowed_methods = ['post','get']
        detail_allowed_methods = ['post','get']

"""""