"""Admin."""
from django.contrib import admin

# Register your models here.
from .models import AuthUser, Municipalities, PredefinedNotification


admin.site.register(PredefinedNotification)
