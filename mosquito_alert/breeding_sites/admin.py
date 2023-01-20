from django.contrib import admin

from .models import BreedingSite


# Register your models here.
class BreedingSiteAdmin(admin.ModelAdmin):
    pass


admin.site.register(BreedingSite, BreedingSiteAdmin)
