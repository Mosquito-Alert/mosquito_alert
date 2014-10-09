from django.db import models
from tigaserver_app.models import Photo


class CrowdcraftingTask(models.Model):
    task_id = models.IntegerField(primary_key=True)
    photo = models.OneToOneField(Photo)

    def __unicode__(self):
        return str(self.task_id)


class CrowdcraftingUser(models.Model):
    user_id = models.IntegerField(primary_key=True)

    def __unicode__(self):
        return str(self.id)


class CrowdcraftingResponse(models.Model):
    task = models.ForeignKey(CrowdcraftingTask, related_name="responses")
    user = models.ForeignKey(CrowdcraftingUser, related_name="responses")
    user_lang = models.CharField(max_length=2, blank=True)
    mosquito_question_response = models.CharField(max_length=100)
    tiger_question_response = models.CharField(max_length=100)
    site_question_response = models.CharField(max_length=100)
    created = models.DateTimeField()
    finish_time = models.DateTimeField()
    user_ip = models.IPAddressField()

    def __unicode__(self):
        return str(self.id)
