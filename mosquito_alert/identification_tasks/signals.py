from django.db.models.signals import post_save
from django.dispatch import receiver

from mosquito_alert.reports.models import Report, Photo

from .models import IdentificationTask


@receiver(post_save, sender=Photo)
def handle_new_photo_creation(sender, instance: Photo, created: bool, **kwargs):
    if not created:
        return

    if instance.report.type == Report.TYPE_ADULT:
        IdentificationTask.get_or_create_for_report(report=instance.report)
