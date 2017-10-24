from django.contrib import admin
from django.contrib.admin import SimpleListFilter

# Register your models here.
from .models import Municipalities, UserMunicipalities

class MunicipalitiesAdmin(admin.ModelAdmin):

    def get_queryset(self, request):
        qs = super(MunicipalitiesAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs.filter(tipo='Municipio')
        return qs.filter(tipo='Municipio')

class UserMunicipalitiesAdmin(admin.ModelAdmin):
    list_filter = ('user', )

admin.site.register(UserMunicipalities, UserMunicipalitiesAdmin)
