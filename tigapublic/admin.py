"""Admin."""
from django.contrib import admin

# Register your models here.
from .models import AuthUser, Municipalities, PredefinedNotification


class AuthUserAdmin(admin.ModelAdmin):
    """AuthUserAdmin."""

    filter_horizontal = ('province', 'municipalities')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """formfield_for_manytomany."""
        if db_field.name == "municipalities":

            editing_user_id = request.resolver_match.kwargs['object_id']

            qs_p = AuthUser.objects.filter(
                id__exact=editing_user_id
            ).values('province__id')

            kwargs["queryset"] = Municipalities.objects.filter(
                codprov__in=qs_p
            )

        return super(AuthUserAdmin, self).formfield_for_manytomany(db_field,
                                                                   request,
                                                                   **kwargs)


admin.site.register(AuthUser, AuthUserAdmin)
admin.site.register(PredefinedNotification)
