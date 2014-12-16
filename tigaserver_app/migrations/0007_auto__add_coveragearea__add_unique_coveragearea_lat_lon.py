# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CoverageArea'
        db.create_table(u'tigaserver_app_coveragearea', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lat', self.gf('django.db.models.fields.FloatField')()),
            ('lon', self.gf('django.db.models.fields.FloatField')()),
            ('n_fixes', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('latest_report_server_upload_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('latest_fix_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'tigaserver_app', ['CoverageArea'])

        # Adding unique constraint on 'CoverageArea', fields ['lat', 'lon']
        db.create_unique(u'tigaserver_app_coveragearea', ['lat', 'lon'])


    def backwards(self, orm):
        # Removing unique constraint on 'CoverageArea', fields ['lat', 'lon']
        db.delete_unique(u'tigaserver_app_coveragearea', ['lat', 'lon'])

        # Deleting model 'CoverageArea'
        db.delete_table(u'tigaserver_app_coveragearea')


    models = {
        u'tigaserver_app.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'samples_per_day': ('django.db.models.fields.IntegerField', [], {})
        },
        u'tigaserver_app.coveragearea': {
            'Meta': {'unique_together': "(('lat', 'lon'),)", 'object_name': 'CoverageArea'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {}),
            'latest_fix_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'latest_report_server_upload_time': ('django.db.models.fields.DateTimeField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {}),
            'n_fixes': ('django.db.models.fields.PositiveIntegerField', [], {})
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
            'user_coverage_uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'null': 'True', 'blank': 'True'})
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
            'mission_version': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
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
            'hide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'photos'", 'to': u"orm['tigaserver_app.Report']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'055a5dc7-e497-47b3-a6e3-5a9c1ffed411'", 'max_length': '36'})
        },
        u'tigaserver_app.report': {
            'Meta': {'unique_together': "(('user', 'version_UUID'),)", 'object_name': 'Report'},
            'app_language': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {}),
            'current_location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'current_location_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'device_manufacturer': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'device_model': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'hide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location_choice': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'mission': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.Mission']", 'null': 'True', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'os': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'os_language': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'os_version': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'package_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '400', 'blank': 'True'}),
            'package_version': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'phone_upload_time': ('django.db.models.fields.DateTimeField', [], {}),
            'report_id': ('django.db.models.fields.CharField', [], {'max_length': '4', 'db_index': 'True'}),
            'selected_location_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'selected_location_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'server_upload_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.TigaUser']"}),
            'version_UUID': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'}),
            'version_number': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
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