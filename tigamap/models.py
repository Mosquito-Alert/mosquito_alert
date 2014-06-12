from django.db import models


class MapString(models.Model):
    nickname = models.CharField(max_length=20, unique=True)
    ca = models.TextField()
    es = models.TextField()
    en = models.TextField()

    def __unicode__(self):
        return str(self.nickname)
