from django.db import models


class Alert(models.Model):
    xvb = models.BooleanField(
        "Stands for expert validation based - if True, means that the alert was sent after expert validation. For False, it was sent before"
    )
    report_id = models.CharField(
        help_text="Report related with the alert", max_length=40
    )
    report_datetime = models.DateTimeField()
    loc_code = models.CharField(
        "Locale code - can be either a nuts3 code, or a nuts3_natcode (natcode is a municipality code) for spanish reports",
        max_length=25,
    )
    cat_id = models.IntegerField("aima species category id")
    species = models.CharField("Species slug", max_length=25)
    certainty = models.FloatField("IA certainty value")
    status = models.CharField("Introduction status label", max_length=50, default="")
    hit = models.BooleanField(
        "True if AIMA identification was initially correct, False if AIMA initially failed and was revised",
        blank=True,
        null=True,
    )
    review_species = models.CharField(
        "Revised species slug, can be empty", max_length=25, blank=True, null=True
    )
    review_status = models.CharField(
        "Revised introduction status label", max_length=50, blank=True, null=True
    )
    review_datetime = models.DateTimeField("revision timestamp", blank=True, null=True)
    alert_sent = models.BooleanField("flag for alert sent or not yet", default=False)
    notes = models.TextField(
        "Notes field for varied observations", blank=True, null=True
    )
