from django.contrib import admin

from .models import Bite


# Register your models here.
class BiteAdmin(admin.ModelAdmin):
    list_display = ("body_part", "datetime", "individual")


admin.site.register(Bite, BiteAdmin)
