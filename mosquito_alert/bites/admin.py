from django.contrib import admin

from .models import Bite


# Register your models here.
@admin.register(Bite)
class BiteAdmin(admin.ModelAdmin):
    list_display = ("body_part", "datetime", "individual")
