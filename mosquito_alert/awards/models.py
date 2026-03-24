from datetime import datetime

from django.contrib.auth import get_user_model
from django.contrib.gis.db import models

from mosquito_alert.reports.models import Report
from mosquito_alert.users.models import TigaUser

from .messaging import send_new_award_notification

User = get_user_model()


class AwardCategory(models.Model):
    category_label = models.TextField(help_text='Coded label for the translated version of the award. For instance award_good_picture. This code refers to strings in several languages')
    xp_points = models.IntegerField(help_text='Number of xp points associated to this kind of award')
    category_long_description = models.TextField(default=None, blank=True, null=True, help_text='Long description specifying conditions in which the award should be conceded')

    class Meta:
        db_table = 'tigaserver_app_awardcategory' # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.


class Award(models.Model):
    report = models.ForeignKey(Report, default=None, blank=True, null=True, related_name='report_award', help_text='Report which the award refers to. Can be blank for arbitrary awards', on_delete=models.CASCADE, )
    date_given = models.DateTimeField(default=datetime.now, help_text='Date in which the award was given')
    given_to = models.ForeignKey(TigaUser, related_name="user_awards", help_text='User to which the notification was awarded. Usually this is the user that uploaded the report, but the report can be blank for special awards', on_delete=models.CASCADE, )
    expert = models.ForeignKey(User, null=True, blank=True, related_name="expert_awards", help_text='Expert that gave the award', on_delete=models.SET_NULL, )
    category = models.ForeignKey(AwardCategory, blank=True, null=True, related_name="category_awards", help_text='Category to which the award belongs. Can be blank for arbitrary awards', on_delete=models.CASCADE, )
    special_award_text = models.TextField(default=None, blank=True, null=True, help_text='Custom text for custom award')
    special_award_xp = models.IntegerField(default=0, blank=True, null=True, help_text='Custom xp awarded')

    def save(self, *args, **kwargs) -> None:
        is_adding = self._state.adding

        super().save(*args, **kwargs)

        if is_adding:
            send_new_award_notification(award=self)

        if self.given_to is not None:
            self.given_to.update_score()

    def delete(self, *args, **kwargs):
        if self.given_to is not None:
            self.given_to.update_score()

        return super().delete(*args, **kwargs)

    def __str__(self):
        if self.category:
            return str(self.category.category_label)
        else:
            return self.special_award_text

    class Meta:
        db_table = 'tigaserver_app_award' # NOTE: migrate from old tigaserver_app, kept old name to avoid issues with custom third-party scripts that still uses the raw table name.
