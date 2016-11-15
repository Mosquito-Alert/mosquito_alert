extra config from settings-development.py
[Errno 2] No such file or directory: '/home2/abusquets/sigte/projectes/mosquito/www/tigatrapp/tigaserver_project/settings-development.py'
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
from __future__ import unicode_literals

from django.db import models

class AuthGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=80)
    class Meta:
        managed = False
        db_table = 'auth_group'

class AuthGroupPermissions(models.Model):
    id = models.IntegerField(primary_key=True)
    group = models.ForeignKey(AuthGroup)
    permission = models.ForeignKey('AuthPermission')
    class Meta:
        managed = False
        db_table = 'auth_group_permissions'

class AuthPermission(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    content_type = models.ForeignKey('DjangoContentType')
    codename = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'auth_permission'

class AuthUser(models.Model):
    id = models.IntegerField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField()
    is_superuser = models.BooleanField()
    username = models.CharField(max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=75)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'auth_user'

class AuthUserGroups(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(AuthUser)
    group = models.ForeignKey(AuthGroup)
    class Meta:
        managed = False
        db_table = 'auth_user_groups'

class AuthUserUserPermissions(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(AuthUser)
    permission = models.ForeignKey(AuthPermission)
    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'

class AuthtokenToken(models.Model):
    key = models.CharField(max_length=40)
    user = models.ForeignKey(AuthUser, unique=True)
    created = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'authtoken_token'

class DjangoAdminLog(models.Model):
    id = models.IntegerField(primary_key=True)
    action_time = models.DateTimeField()
    user = models.ForeignKey(AuthUser)
    content_type = models.ForeignKey('DjangoContentType', blank=True, null=True)
    object_id = models.TextField(blank=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    class Meta:
        managed = False
        db_table = 'django_admin_log'

class DjangoContentType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'django_content_type'

class DjangoSession(models.Model):
    session_key = models.CharField(max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'django_session'

class GeographyColumns(models.Model):
    f_table_catalog = models.TextField(blank=True) # This field type is a guess.
    f_table_schema = models.TextField(blank=True) # This field type is a guess.
    f_table_name = models.TextField(blank=True) # This field type is a guess.
    f_geography_column = models.TextField(blank=True) # This field type is a guess.
    coord_dimension = models.IntegerField(blank=True, null=True)
    srid = models.IntegerField(blank=True, null=True)
    type = models.TextField(blank=True)
    class Meta:
        managed = False
        db_table = 'geography_columns'

class GeometryColumns(models.Model):
    f_table_catalog = models.CharField(max_length=256, blank=True)
    f_table_schema = models.CharField(max_length=256, blank=True)
    f_table_name = models.CharField(max_length=256, blank=True)
    f_geometry_column = models.CharField(max_length=256, blank=True)
    coord_dimension = models.IntegerField(blank=True, null=True)
    srid = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=30, blank=True)
    class Meta:
        managed = False
        db_table = 'geometry_columns'

class MapAuxReports(models.Model):
    id = models.IntegerField(primary_key=True)
    version_uuid = models.CharField(max_length=36, blank=True)
    observation_date = models.DateTimeField(blank=True, null=True)
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    ref_system = models.CharField(max_length=36, blank=True)
    type = models.CharField(max_length=7, blank=True)
    breeding_site_answers = models.CharField(max_length=100, blank=True)
    mosquito_answers = models.CharField(max_length=100, blank=True)
    expert_validated = models.NullBooleanField()
    expert_validation_result = models.CharField(max_length=100, blank=True)
    simplified_expert_validation_result = models.CharField(max_length=100, blank=True)
    site_cat = models.IntegerField(blank=True, null=True)
    storm_drain_status = models.CharField(max_length=50, blank=True)
    edited_user_notes = models.CharField(max_length=4000, blank=True)
    photo_url = models.CharField(max_length=255, blank=True)
    photo_license = models.CharField(max_length=100, blank=True)
    dataset_license = models.CharField(max_length=100, blank=True)
    class Meta:
        managed = False
        db_table = 'map_aux_reports'

class RasterColumns(models.Model):
    r_table_catalog = models.TextField(blank=True) # This field type is a guess.
    r_table_schema = models.TextField(blank=True) # This field type is a guess.
    r_table_name = models.TextField(blank=True) # This field type is a guess.
    r_raster_column = models.TextField(blank=True) # This field type is a guess.
    srid = models.IntegerField(blank=True, null=True)
    scale_x = models.FloatField(blank=True, null=True)
    scale_y = models.FloatField(blank=True, null=True)
    blocksize_x = models.IntegerField(blank=True, null=True)
    blocksize_y = models.IntegerField(blank=True, null=True)
    same_alignment = models.NullBooleanField()
    regular_blocking = models.NullBooleanField()
    num_bands = models.IntegerField(blank=True, null=True)
    pixel_types = models.TextField(blank=True) # This field type is a guess.
    nodata_values = models.TextField(blank=True) # This field type is a guess.
    out_db = models.TextField(blank=True) # This field type is a guess.
    extent = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        managed = False
        db_table = 'raster_columns'

class RasterOverviews(models.Model):
    o_table_catalog = models.TextField(blank=True) # This field type is a guess.
    o_table_schema = models.TextField(blank=True) # This field type is a guess.
    o_table_name = models.TextField(blank=True) # This field type is a guess.
    o_raster_column = models.TextField(blank=True) # This field type is a guess.
    r_table_catalog = models.TextField(blank=True) # This field type is a guess.
    r_table_schema = models.TextField(blank=True) # This field type is a guess.
    r_table_name = models.TextField(blank=True) # This field type is a guess.
    r_raster_column = models.TextField(blank=True) # This field type is a guess.
    overview_factor = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'raster_overviews'

class Report(models.Model):
    version_uuid = models.CharField(primary_key=True, max_length=36)
    creation_time = models.DateTimeField(blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    creation_day_since_launch = models.IntegerField(blank=True, null=True)
    creation_year = models.IntegerField(blank=True, null=True)
    creation_month = models.IntegerField(blank=True, null=True)
    site_cat = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=50, blank=True)
    lon = models.FloatField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True)
    movelab_annotation = models.TextField(blank=True)
    tiger_responses = models.TextField(blank=True)
    site_responses = models.TextField(blank=True)
    tigaprob_cat = models.IntegerField(blank=True, null=True)
    visible = models.NullBooleanField()
    latest_version = models.NullBooleanField()
    field_type = models.CharField(db_column='_type', max_length=5, blank=True) # Field renamed because it started with '_'.
    class Meta:
        managed = False
        db_table = 'report'

class SouthMigrationhistory(models.Model):
    id = models.IntegerField(primary_key=True)
    app_name = models.CharField(max_length=255)
    migration = models.CharField(max_length=255)
    applied = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'south_migrationhistory'

class SpatialRefSys(models.Model):
    srid = models.IntegerField(primary_key=True)
    auth_name = models.CharField(max_length=256, blank=True)
    auth_srid = models.IntegerField(blank=True, null=True)
    srtext = models.CharField(max_length=2048, blank=True)
    proj4text = models.CharField(max_length=2048, blank=True)
    class Meta:
        managed = False
        db_table = 'spatial_ref_sys'

class TigacraftingAnnotation(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(AuthUser)
    task = models.ForeignKey('TigacraftingCrowdcraftingtask')
    tiger_certainty_percent = models.IntegerField(blank=True, null=True)
    notes = models.TextField()
    last_modified = models.DateTimeField()
    created = models.DateTimeField()
    working_on = models.BooleanField()
    value_changed = models.BooleanField()
    class Meta:
        managed = False
        db_table = 'tigacrafting_annotation'

class TigacraftingCrowdcraftingresponse(models.Model):
    id = models.IntegerField(primary_key=True)
    response_id = models.IntegerField()
    task = models.ForeignKey('TigacraftingCrowdcraftingtask')
    user = models.ForeignKey('TigacraftingCrowdcraftinguser', blank=True, null=True)
    user_lang = models.CharField(max_length=10)
    mosquito_question_response = models.CharField(max_length=100)
    tiger_question_response = models.CharField(max_length=100)
    site_question_response = models.CharField(max_length=100)
    created = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'tigacrafting_crowdcraftingresponse'

class TigacraftingCrowdcraftingtask(models.Model):
    id = models.IntegerField(primary_key=True)
    task_id = models.IntegerField(unique=True, blank=True, null=True)
    photo_id = models.IntegerField(unique=True)
    class Meta:
        managed = False
        db_table = 'tigacrafting_crowdcraftingtask'

class TigacraftingCrowdcraftinguser(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'tigacrafting_crowdcraftinguser'

class TigacraftingExpertreportannotation(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(AuthUser)
    report = models.ForeignKey('TigaserverAppReport')
    tiger_certainty_category = models.IntegerField(blank=True, null=True)
    tiger_certainty_notes = models.TextField()
    site_certainty_category = models.IntegerField(blank=True, null=True)
    site_certainty_notes = models.TextField()
    edited_user_notes = models.TextField()
    last_modified = models.DateTimeField()
    created = models.DateTimeField()
    validation_complete = models.BooleanField()
    best_photo = models.ForeignKey('TigaserverAppPhoto', blank=True, null=True)
    linked_id = models.CharField(max_length=10)
    message_for_user = models.TextField()
    status = models.IntegerField()
    revise = models.BooleanField()
    aegypti_certainty_category = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'tigacrafting_expertreportannotation'

class TigacraftingMovelabannotation(models.Model):
    id = models.IntegerField(primary_key=True)
    task = models.ForeignKey(TigacraftingCrowdcraftingtask, unique=True)
    tiger_certainty_category = models.IntegerField(blank=True, null=True)
    certainty_notes = models.TextField()
    hide = models.BooleanField()
    edited_user_notes = models.TextField()
    last_modified = models.DateTimeField()
    created = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'tigacrafting_movelabannotation'

class TigacraftingUserstat(models.Model):
    user = models.ForeignKey(AuthUser, primary_key=True)
    class Meta:
        managed = False
        db_table = 'tigacrafting_userstat'

class TigamapMapstring(models.Model):
    id = models.IntegerField(primary_key=True)
    nickname = models.CharField(max_length=20)
    ca = models.TextField()
    es = models.TextField()
    en = models.TextField()
    class Meta:
        managed = False
        db_table = 'tigamap_mapstring'

class TigaserverAppConfiguration(models.Model):
    id = models.IntegerField(primary_key=True)
    samples_per_day = models.IntegerField()
    creation_time = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'tigaserver_app_configuration'

class TigaserverAppCoveragearea(models.Model):
    id = models.IntegerField(primary_key=True)
    lat = models.FloatField()
    lon = models.FloatField()
    n_fixes = models.IntegerField()
    last_modified = models.DateTimeField()
    latest_report_server_upload_time = models.DateTimeField()
    latest_fix_id = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'tigaserver_app_coveragearea'

class TigaserverAppCoverageareamonth(models.Model):
    id = models.IntegerField(primary_key=True)
    lat = models.FloatField()
    lon = models.FloatField()
    year = models.IntegerField()
    month = models.IntegerField()
    n_fixes = models.IntegerField()
    last_modified = models.DateTimeField()
    latest_report_server_upload_time = models.DateTimeField()
    latest_fix_id = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'tigaserver_app_coverageareamonth'

class TigaserverAppFix(models.Model):
    id = models.IntegerField(primary_key=True)
    fix_time = models.DateTimeField()
    server_upload_time = models.DateTimeField()
    phone_upload_time = models.DateTimeField()
    masked_lon = models.FloatField()
    masked_lat = models.FloatField()
    power = models.FloatField(blank=True, null=True)
    user_coverage_uuid = models.CharField(max_length=36, blank=True)
    class Meta:
        managed = False
        db_table = 'tigaserver_app_fix'

class TigaserverAppMission(models.Model):
    id = models.IntegerField(primary_key=True)
    title_catalan = models.CharField(max_length=200)
    title_spanish = models.CharField(max_length=200)
    title_english = models.CharField(max_length=200)
    short_description_catalan = models.CharField(max_length=200)
    short_description_spanish = models.CharField(max_length=200)
    short_description_english = models.CharField(max_length=200)
    long_description_catalan = models.CharField(max_length=1000)
    long_description_spanish = models.CharField(max_length=1000)
    long_description_english = models.CharField(max_length=1000)
    help_text_catalan = models.TextField()
    help_text_spanish = models.TextField()
    help_text_english = models.TextField()
    platform = models.CharField(max_length=4)
    creation_time = models.DateTimeField()
    expiration_time = models.DateTimeField(blank=True, null=True)
    photo_mission = models.BooleanField()
    url = models.CharField(max_length=200)
    mission_version = models.IntegerField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'tigaserver_app_mission'

class TigaserverAppMissionitem(models.Model):
    id = models.IntegerField(primary_key=True)
    mission = models.ForeignKey(TigaserverAppMission)
    question_catalan = models.CharField(max_length=1000)
    question_spanish = models.CharField(max_length=1000)
    question_english = models.CharField(max_length=1000)
    answer_choices_catalan = models.CharField(max_length=1000)
    answer_choices_spanish = models.CharField(max_length=1000)
    answer_choices_english = models.CharField(max_length=1000)
    help_text_catalan = models.TextField()
    help_text_spanish = models.TextField()
    help_text_english = models.TextField()
    prepositioned_image_reference = models.IntegerField(blank=True, null=True)
    attached_image = models.CharField(max_length=100, blank=True)
    class Meta:
        managed = False
        db_table = 'tigaserver_app_missionitem'

class TigaserverAppMissiontrigger(models.Model):
    id = models.IntegerField(primary_key=True)
    mission = models.ForeignKey(TigaserverAppMission)
    lat_lower_bound = models.FloatField(blank=True, null=True)
    lat_upper_bound = models.FloatField(blank=True, null=True)
    lon_lower_bound = models.FloatField(blank=True, null=True)
    lon_upper_bound = models.FloatField(blank=True, null=True)
    time_lowerbound = models.TimeField(blank=True, null=True)
    time_upperbound = models.TimeField(blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'tigaserver_app_missiontrigger'

class TigaserverAppPhoto(models.Model):
    id = models.IntegerField(primary_key=True)
    photo = models.CharField(max_length=100)
    report = models.ForeignKey('TigaserverAppReport')
    hide = models.BooleanField()
    uuid = models.CharField(max_length=36)
    class Meta:
        managed = False
        db_table = 'tigaserver_app_photo'

class TigaserverAppReport(models.Model):
    version_uuid = models.CharField(db_column='version_UUID', max_length=36) # Field name made lowercase.
    version_number = models.IntegerField()
    user = models.ForeignKey('TigaserverAppTigauser')
    report_id = models.CharField(max_length=4)
    server_upload_time = models.DateTimeField()
    phone_upload_time = models.DateTimeField()
    creation_time = models.DateTimeField()
    version_time = models.DateTimeField()
    type = models.CharField(max_length=7)
    mission = models.ForeignKey(TigaserverAppMission, blank=True, null=True)
    location_choice = models.CharField(max_length=8)
    current_location_lon = models.FloatField(blank=True, null=True)
    current_location_lat = models.FloatField(blank=True, null=True)
    selected_location_lon = models.FloatField(blank=True, null=True)
    selected_location_lat = models.FloatField(blank=True, null=True)
    note = models.TextField()
    package_name = models.CharField(max_length=400)
    package_version = models.IntegerField(blank=True, null=True)
    device_manufacturer = models.CharField(max_length=200)
    device_model = models.CharField(max_length=200)
    os = models.CharField(max_length=200)
    os_version = models.CharField(max_length=200)
    os_language = models.CharField(max_length=10)
    app_language = models.CharField(max_length=10)
    hide = models.BooleanField()
    class Meta:
        managed = False
        db_table = 'tigaserver_app_report'

class TigaserverAppReportProva(models.Model):
    version_uuid = models.CharField(db_column='version_UUID', max_length=36, blank=True) # Field name made lowercase.
    version_number = models.IntegerField(blank=True, null=True)
    user_id = models.CharField(max_length=36, blank=True)
    report_id = models.CharField(max_length=4, blank=True)
    server_upload_time = models.DateTimeField(blank=True, null=True)
    phone_upload_time = models.DateTimeField(blank=True, null=True)
    creation_time = models.DateTimeField(blank=True, null=True)
    version_time = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=7, blank=True)
    mission_id = models.IntegerField(blank=True, null=True)
    location_choice = models.CharField(max_length=8, blank=True)
    current_location_lon = models.FloatField(blank=True, null=True)
    current_location_lat = models.FloatField(blank=True, null=True)
    selected_location_lon = models.FloatField(blank=True, null=True)
    selected_location_lat = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True)
    package_name = models.CharField(max_length=400, blank=True)
    package_version = models.IntegerField(blank=True, null=True)
    device_manufacturer = models.CharField(max_length=200, blank=True)
    device_model = models.CharField(max_length=200, blank=True)
    os = models.CharField(max_length=200, blank=True)
    os_version = models.CharField(max_length=200, blank=True)
    os_language = models.CharField(max_length=10, blank=True)
    app_language = models.CharField(max_length=10, blank=True)
    hide = models.NullBooleanField()
    field_type = models.CharField(db_column='_type', max_length=5, blank=True) # Field renamed because it started with '_'.
    class Meta:
        managed = False
        db_table = 'tigaserver_app_report_prova'

class TigaserverAppReportresponse(models.Model):
    id = models.IntegerField(primary_key=True)
    report = models.ForeignKey(TigaserverAppReport)
    question = models.CharField(max_length=1000)
    answer = models.CharField(max_length=1000)
    class Meta:
        managed = False
        db_table = 'tigaserver_app_reportresponse'

class TigaserverAppTigauser(models.Model):
    user_uuid = models.CharField(db_column='user_UUID', max_length=36) # Field name made lowercase.
    registration_time = models.DateTimeField()
    class Meta:
        managed = False
        db_table = 'tigaserver_app_tigauser'

class Tiles(models.Model):
    id = models.IntegerField(primary_key=True)
    x = models.IntegerField(blank=True, null=True)
    y = models.IntegerField(blank=True, null=True)
    z = models.IntegerField(blank=True, null=True)
    geom = models.TextField(blank=True) # This field type is a guess.
    ids = models.TextField(blank=True)
    c = models.CharField(max_length=10, blank=True)
    class Meta:
        managed = False
        db_table = 'tiles'

