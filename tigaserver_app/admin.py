from django.contrib import admin
from tigaserver_app.models import TigaUser, Report, Mission, Photo

admin.site.register(TigaUser)
admin.site.register(Report)
admin.site.register(Mission)
admin.site.register(Photo)
