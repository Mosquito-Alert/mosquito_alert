from django.contrib import admin

from .models import BreedingSite


# Register your models here.
@admin.register(BreedingSite)
class BreedingSiteAdmin(admin.ModelAdmin):
    pass
