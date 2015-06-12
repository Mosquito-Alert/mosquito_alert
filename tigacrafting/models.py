from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.core.validators import MaxValueValidator, MinValueValidator


def score_computation(n_total, n_yes, n_no, n_unknown = 0, n_undefined =0):
    return float(n_yes - n_no)/n_total


class CrowdcraftingTask(models.Model):
    task_id = models.IntegerField(unique=True, null=True, default=None)
    photo = models.OneToOneField('tigaserver_app.Photo')

    def __unicode__(self):
        return str(self.task_id)

    def get_mosquito_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_tiger_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-no').count() + CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='undefined', mosquito_question_response='mosquito-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_tiger_validation_score_cat(self):
        if self.get_tiger_validation_score() is not None:
            return int(round(2.499999 * self.get_tiger_validation_score(), 0))
        else:
            return None

    def get_site_validation_score(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_yes = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-yes').count()
            n_no = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-no').count()
            return score_computation(n_total=n_total, n_yes=n_yes, n_no=n_no)

    def get_site_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-no').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-no').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='site-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, site_question_response='undefined').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, site_question_response='site-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, site_question_response='undefined').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_tiger_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-no').count() + CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-no', tiger_question_response='undefined').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-no').exclude(user__user_id=None).count() + CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no', tiger_question_response='undefined').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='tiger-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, tiger_question_response='undefined').exclude(mosquito_question_response='mosquito-no').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='tiger-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, tiger_question_response='undefined').exclude(mosquito_question_response='mosquito-no').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_mosquito_individual_responses_html(self):
        n_total = CrowdcraftingResponse.objects.filter(task=self).count()
        if n_total == 0:
            return None
        else:
            n_anon_yes = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-yes').count()
            n_anon_no = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-no').count()
            n_reg_yes = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-yes').exclude(user__user_id=None).count()
            n_reg_no = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-no').exclude(user__user_id=None).count()
            n_anon_unknown = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='mosquito-unknown').count()
            n_anon_blank = CrowdcraftingResponse.objects.filter(task=self, user__user_id=None, mosquito_question_response='undefined').count()
            n_reg_unknown = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='mosquito-unknown').exclude(user__user_id=None).count()
            n_reg_blank = CrowdcraftingResponse.objects.filter(task=self, mosquito_question_response='undefined').exclude(user__user_id=None).count()
            return '<table><tr><th>Resp.</th><th>Reg. Users</th><th>Anon. Users</th><th>Total</th></tr><tr><td>Yes</td><td>' + str(n_reg_yes) + '</td><td>' + str(n_anon_yes) + '</td><td>' + str(n_reg_yes + n_anon_yes) + '</td></tr><tr><td>No</td><td>' + str(n_reg_no) + '</td><td>' + str(n_anon_no) + '</td><td>' + str(n_reg_no + n_anon_no) + '</td></tr><tr><td>Not sure</td><td>' + str(n_reg_unknown) + '</td><td>' + str(n_anon_unknown) + '</td><td>' + str(0 + n_reg_unknown + n_anon_unknown) + '</td></tr><tr><td>Blank</td><td>' + str(n_reg_blank) + '</td><td>' + str(n_anon_blank) + '</td><td>' + str(n_reg_blank + n_anon_blank) + '</td></tr><tr><td>Total</td><td>' + str(n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank) + '</td><td>' + str(n_anon_yes + n_anon_no + n_anon_unknown + n_anon_blank + n_reg_yes + n_reg_no + n_reg_unknown + n_reg_blank) + '</td></tr></table>'

    def get_crowdcrafting_n_responses(self):
        return CrowdcraftingResponse.objects.filter(task=self).count()

    mosquito_validation_score = property(get_mosquito_validation_score)
    tiger_validation_score = property(get_tiger_validation_score)
    site_validation_score = property(get_site_validation_score)
    site_individual_responses_html = property(get_site_individual_responses_html)
    tiger_individual_responses_html = property(get_tiger_individual_responses_html)
    mosquito_individual_responses_html = property(get_mosquito_individual_responses_html)
    crowdcrafting_n_responses = property(get_crowdcrafting_n_responses)
    tiger_validation_score_cat = property(get_tiger_validation_score_cat)


class CrowdcraftingUser(models.Model):
    user_id = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return str(self.id)


class CrowdcraftingResponse(models.Model):
    response_id = models.IntegerField()
    task = models.ForeignKey(CrowdcraftingTask, related_name="responses")
    user = models.ForeignKey(CrowdcraftingUser, related_name="responses", blank=True, null=True)
    user_lang = models.CharField(max_length=2, blank=True)
    mosquito_question_response = models.CharField(max_length=100)
    tiger_question_response = models.CharField(max_length=100)
    site_question_response = models.CharField(max_length=100)
    created = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    user_ip = models.IPAddressField(blank=True, null=True)

    def __unicode__(self):
        return str(self.id)


class Annotation(models.Model):
    user = models.ForeignKey(User, related_name='annotations')
    task = models.ForeignKey(CrowdcraftingTask, related_name='annotations')
    tiger_certainty_percent = models.IntegerField('Degree of belief', validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True, null=True)
    value_changed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True, default=datetime.now())
    created = models.DateTimeField(auto_now_add=True, default=datetime.now())
    working_on = models.BooleanField(default=False)

    def __unicode__(self):
        return "Annotation: " + str(self.id) + ", Task: " + str(self.task.task_id)


class MoveLabAnnotation(models.Model):
    task = models.OneToOneField(CrowdcraftingTask, related_name='movelab_annotation')
    CATEGORIES = ((-2, 'Definitely not a tiger mosquito'), (-1, 'Probably not a tiger mosquito'), (0, 'Not sure'), (1, 'Probably a tiger mosquito'), (2, 'Definitely a tiger mosquito'))
    tiger_certainty_category = models.IntegerField('Certainty', choices=CATEGORIES, blank=True, null=True)
    certainty_notes = models.TextField(blank=True)
    hide = models.BooleanField('Hide photo from public', default=False)
    edited_user_notes = models.TextField(blank=True)
    last_modified = models.DateTimeField(auto_now=True, default=datetime.now())
    created = models.DateTimeField(auto_now_add=True, default=datetime.now())


class ExpertReportAnnotation(models.Model):
    user = models.ForeignKey(User, related_name="expert_report_annotations")
    report = models.ForeignKey('tigaserver_app.Report', related_name='expert_report_annotations')
    TIGER_CATEGORIES = ((-2, 'Definitely not a tiger mosquito'), (-1, 'Probably not a tiger mosquito'), (0, 'Not sure'), (1, 'Probably a tiger mosquito'), (2, 'Definitely a tiger mosquito'))
    tiger_certainty_category = models.IntegerField('Tiger Certainty', choices=TIGER_CATEGORIES, blank=True, null=True)
    tiger_certainty_notes = models.TextField(blank=True)
    SITE_CATEGORIES = ((-2, 'Definitely not a breeding site'), (-1, 'Probably not a breeding site'), (0, 'Not sure'), (1, 'Probably a breeding site'), (2, 'Definitely a breeding site'))
    site_certainty_category = models.IntegerField('Site Certainty', choices=SITE_CATEGORIES, blank=True, null=True)
    site_certainty_notes = models.TextField(blank=True)
    edited_user_notes = models.TextField(blank=True)
    flag = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True, default=datetime.now())
    created = models.DateTimeField(auto_now_add=True, default=datetime.now())

    def get_others_annotation_html(self):
        result = ''
        this_user = self.user
        this_report = self.report
        other_annotations = ExpertReportAnnotation.objects.filter(report=this_report).exclude(user=this_user)
        for ano in other_annotations.all():
            result += '<p>User: ' + ano.user.username + ', Last Edited: ' + str(ano.last_modified) + '</p>'
            result += '<p>Tiger Certainty: ' + str(ano.tiger_certainty_category) + '</p>'
            result += '<p>Tiger Notes: ' + ano.tiger_certainty_notes + '</p>'
            result += '<p>Site Certainty: ' + str(ano.site_certainty_category) + '</p>'
            result += '<p>Site Notes: ' + ano.site_certainty_notes + '</p>'
            result += '<p>Flagged?: ' + str(ano.flag) + '</p><hr>'
        return result
