from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import decorators, get_user_model
from django.utils.translation import gettext_lazy as _

from mosquito_alert.identifications.base_admin import BaseIdentifierProfileAdmin
from mosquito_alert.users.forms import UserAdminChangeForm, UserAdminCreationForm

from .models import UserProfile

User = get_user_model()

if settings.DJANGO_ADMIN_FORCE_ALLAUTH:
    # Force the `admin` sign in process to go through the `django-allauth` workflow:
    # https://django-allauth.readthedocs.io/en/stable/advanced.html#admin
    admin.site.login = decorators.login_required(admin.site.login)  # type: ignore[method-assign]


class UserProfileAdminInline(BaseIdentifierProfileAdmin, admin.StackedInline):
    model = UserProfile
    max_num = 1
    can_delete = False

    fields = None
    fieldsets = BaseIdentifierProfileAdmin.fieldsets


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "name", "email", "is_staff", "is_superuser"]
    search_fields = ["username", "name", "email"]

    def add_view(self, *args, **kwargs):
        self.inlines = []
        return super().add_view(*args, **kwargs)

    def change_view(self, *args, **kwargs):
        self.inlines = [UserProfileAdminInline]
        return super().change_view(*args, **kwargs)
