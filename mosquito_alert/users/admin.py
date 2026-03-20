from django.contrib import admin
from mosquito_alert.tigaserver_app.models import NutsEurope
from django.utils.translation import gettext_lazy as _

from .models import UserStat

@admin.register(UserStat)
class UserStatAdmin(admin.ModelAdmin):
    search_fields = ('user__username',)
    ordering = ('user__username',)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "nuts2_assignation":
            kwargs["queryset"] = NutsEurope.objects.all().order_by('europecountry__name_engl','name_latn')
        return super(UserStatAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
