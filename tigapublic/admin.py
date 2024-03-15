"""Admin."""
from django.contrib import admin

# Register your models here.
from .models import PredefinedNotification

admin.site.register(PredefinedNotification)
