# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TigaUser'
        db.create_table(u'tigaserver_app_tigauser', (
            ('user_UUID', self.gf('django.db.models.fields.CharField')(max_length=36, primary_key=True)),
            ('registration_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['TigaUser'])

        # Adding model 'Mission'
        db.create_table(u'tigaserver_app_mission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title_catalan', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title_spanish', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('title_english', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('short_description_catalan', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('short_description_spanish', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('short_description_english', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('long_description_catalan', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('long_description_spanish', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('long_description_english', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('help_text_catalan', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('help_text_spanish', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('help_text_english', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('platform', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('expiration_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('photo_mission', self.gf('django.db.models.fields.BooleanField')()),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['Mission'])

        # Adding model 'MissionTrigger'
        db.create_table(u'tigaserver_app_missiontrigger', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='triggers', to=orm['tigaserver_app.Mission'])),
            ('lat_lower_bound', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('lat_upper_bound', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('lon_lower_bound', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('lon_upper_bound', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('time_lowerbound', self.gf('django.db.models.fields.TimeField')(null=True, blank=True)),
            ('time_upperbound', self.gf('django.db.models.fields.TimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['MissionTrigger'])

        # Adding model 'MissionItem'
        db.create_table(u'tigaserver_app_missionitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mission', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['tigaserver_app.Mission'])),
            ('question_catalan', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('question_spanish', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('question_english', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('answer_choices_catalan', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('answer_choices_spanish', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('answer_choices_english', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('help_text_catalan', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('help_text_spanish', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('help_text_english', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('prepositioned_image_reference', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('attached_image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['MissionItem'])

        # Adding model 'Report'
        db.create_table(u'tigaserver_app_report', (
            ('version_UUID', self.gf('django.db.models.fields.CharField')(max_length=36, primary_key=True)),
            ('version_number', self.gf('django.db.models.fields.IntegerField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigaserver_app.TigaUser'])),
            ('report_id', self.gf('django.db.models.fields.CharField')(max_length=4)),
            ('server_upload_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('phone_upload_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('version_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=7)),
            ('mission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigaserver_app.Mission'], null=True, blank=True)),
            ('location_choice', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('current_location_lon', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('current_location_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('selected_location_lon', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('selected_location_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('package_name', self.gf('django.db.models.fields.CharField')(max_length=400, blank=True)),
            ('package_version', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('device_manufacturer', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('device_model', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('os', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('os_version', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('os_language', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('app_language', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['Report'])

        # Adding unique constraint on 'Report', fields ['user', 'version_UUID']
        db.create_unique(u'tigaserver_app_report', ['user_id', 'version_UUID'])

        # Adding model 'ReportResponse'
        db.create_table(u'tigaserver_app_reportresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['tigaserver_app.Report'])),
            ('question', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('answer', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal(u'tigaserver_app', ['ReportResponse'])

        # Adding model 'Photo'
        db.create_table(u'tigaserver_app_photo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('photo', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigaserver_app.Report'])),
        ))
        db.send_create_signal(u'tigaserver_app', ['Photo'])

        # Adding model 'Fix'
        db.create_table(u'tigaserver_app_fix', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigaserver_app.TigaUser'])),
            ('fix_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('server_upload_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('phone_upload_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('masked_lon', self.gf('django.db.models.fields.FloatField')()),
            ('masked_lat', self.gf('django.db.models.fields.FloatField')()),
            ('power', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['Fix'])

        # Adding model 'Configuration'
        db.create_table(u'tigaserver_app_configuration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('samples_per_day', self.gf('django.db.models.fields.IntegerField')()),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'tigaserver_app', ['Configuration'])


    def backwards(self, orm):
        # Removing unique constraint on 'Report', fields ['user', 'version_UUID']
        db.delete_unique(u'tigaserver_app_report', ['user_id', 'version_UUID'])

        # Deleting model 'TigaUser'
        db.delete_table(u'tigaserver_app_tigauser')

        # Deleting model 'Mission'
        db.delete_table(u'tigaserver_app_mission')

        # Deleting model 'MissionTrigger'
        db.delete_table(u'tigaserver_app_missiontrigger')

        # Deleting model 'MissionItem'
        db.delete_table(u'tigaserver_app_missionitem')

        # Deleting model 'Report'
        db.delete_table(u'tigaserver_app_report')

        # Deleting model 'ReportResponse'
        db.delete_table(u'tigaserver_app_reportresponse')

        # Deleting model 'Photo'
        db.delete_table(u'tigaserver_app_photo')

        # Deleting model 'Fix'
        db.delete_table(u'tigaserver_app_fix')

        # Deleting model 'Configuration'
        db.delete_table(u'tigaserver_app_configuration')


    models = {
        u'tigaserver_app.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'samples_per_day': ('django.db.models.fields.IntegerField', [], {})
        },
        u'tigaserver_app.fix': {
            'Meta': {'object_name': 'Fix'},
            'fix_time': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'masked_lat': ('django.db.models.fields.FloatField', [], {}),
            'masked_lon': ('django.db.models.fields.FloatField', [], {}),
            'phone_upload_time': ('django.db.models.fields.DateTimeField', [], {}),
            'power': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'server_upload_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.TigaUser']"})
        },
        u'tigaserver_app.mission': {
            'Meta': {'object_name': 'Mission'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'expiration_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'help_text_catalan': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'help_text_english': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'help_text_spanish': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description_catalan': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'long_description_english': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'long_description_spanish': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'photo_mission': ('django.db.models.fields.BooleanField', [], {}),
            'platform': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'short_description_catalan': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'short_description_english': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'short_description_spanish': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title_catalan': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title_english': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'title_spanish': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'tigaserver_app.missionitem': {
            'Meta': {'object_name': 'MissionItem'},
            'answer_choices_catalan': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'answer_choices_english': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'answer_choices_spanish': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'attached_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'help_text_catalan': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'help_text_english': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'help_text_spanish': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['tigaserver_app.Mission']"}),
            'prepositioned_image_reference': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'question_catalan': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'question_english': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'question_spanish': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        u'tigaserver_app.missiontrigger': {
            'Meta': {'object_name': 'MissionTrigger'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat_lower_bound': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lat_upper_bound': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lon_lower_bound': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lon_upper_bound': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mission': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'triggers'", 'to': u"orm['tigaserver_app.Mission']"}),
            'time_lowerbound': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'time_upperbound': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tigaserver_app.photo': {
            'Meta': {'object_name': 'Photo'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.Report']"})
        },
        u'tigaserver_app.report': {
            'Meta': {'unique_together': "(('user', 'version_UUID'),)", 'object_name': 'Report'},
            'app_language': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {}),
            'current_location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'current_location_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'device_manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'device_model': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'location_choice': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'mission': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.Mission']", 'null': 'True', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'os_language': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'os_version': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'package_name': ('django.db.models.fields.CharField', [], {'max_length': '400', 'blank': 'True'}),
            'package_version': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'phone_upload_time': ('django.db.models.fields.DateTimeField', [], {}),
            'report_id': ('django.db.models.fields.CharField', [], {'max_length': '4'}),
            'selected_location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'selected_location_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'server_upload_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.TigaUser']"}),
            'version_UUID': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'}),
            'version_number': ('django.db.models.fields.IntegerField', [], {}),
            'version_time': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'tigaserver_app.reportresponse': {
            'Meta': {'object_name': 'ReportResponse'},
            'answer': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['tigaserver_app.Report']"})
        },
        u'tigaserver_app.tigauser': {
            'Meta': {'object_name': 'TigaUser'},
            'registration_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_UUID': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'})
        }
    }

    complete_apps = ['tigaserver_app']