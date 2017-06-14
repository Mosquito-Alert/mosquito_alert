# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'StormDrain.idalfa'
        db.delete_column(u'storm_drain', 'idalfa')


        # Changing field 'StormDrain.species1'
        db.alter_column(u'storm_drain', 'species1', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True))

        # Changing field 'StormDrain.municipality'
        db.alter_column(u'storm_drain', 'municipality', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

        # Changing field 'StormDrain.lon'
        db.alter_column(u'storm_drain', 'lon', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=6))

        # Changing field 'StormDrain.water'
        db.alter_column(u'storm_drain', 'water', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True))

        # Changing field 'StormDrain.lat'
        db.alter_column(u'storm_drain', 'lat', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=6))

        # Changing field 'StormDrain.sand'
        db.alter_column(u'storm_drain', 'sand', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True))

        # Changing field 'StormDrain.code'
        db.alter_column(u'storm_drain', 'code', self.gf('django.db.models.fields.CharField')(max_length=50, null=True))

        # Changing field 'StormDrain.species2'
        db.alter_column(u'storm_drain', 'species2', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True))

        # Changing field 'StormDrain.activity'
        db.alter_column(u'storm_drain', 'activity', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True))

        # Changing field 'StormDrain.date'
        db.alter_column(u'storm_drain', 'date', self.gf('django.db.models.fields.DateTimeField')(null=True))

        # Changing field 'StormDrain.model'
        db.alter_column(u'storm_drain', 'model', self.gf('django.db.models.fields.CharField')(max_length=5, null=True))

        # Changing field 'StormDrain.size'
        db.alter_column(u'storm_drain', 'size', self.gf('django.db.models.fields.CharField')(max_length=5, null=True))

        # Changing field 'StormDrain.type'
        db.alter_column(u'storm_drain', 'type', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

        # Changing field 'StormDrain.treatment'
        db.alter_column(u'storm_drain', 'treatment', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True))

    def backwards(self, orm):
        # Adding field 'StormDrain.idalfa'
        db.add_column(u'storm_drain', 'idalfa',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=5, blank=True),
                      keep_default=False)


        # Changing field 'StormDrain.species1'
        db.alter_column(u'storm_drain', 'species1', self.gf('django.db.models.fields.BooleanField')(default=None, max_length=10))

        # Changing field 'StormDrain.municipality'
        db.alter_column(u'storm_drain', 'municipality', self.gf('django.db.models.fields.CharField')(default='', max_length=100))

        # Changing field 'StormDrain.lon'
        db.alter_column(u'storm_drain', 'lon', self.gf('django.db.models.fields.DecimalField')(max_digits=15, decimal_places=6))

        # Changing field 'StormDrain.water'
        db.alter_column(u'storm_drain', 'water', self.gf('django.db.models.fields.BooleanField')(default=None, max_length=10))

        # Changing field 'StormDrain.lat'
        db.alter_column(u'storm_drain', 'lat', self.gf('django.db.models.fields.DecimalField')(max_digits=15, decimal_places=6))

        # Changing field 'StormDrain.sand'
        db.alter_column(u'storm_drain', 'sand', self.gf('django.db.models.fields.BooleanField')(default=None, max_length=10))

        # Changing field 'StormDrain.code'
        db.alter_column(u'storm_drain', 'code', self.gf('django.db.models.fields.CharField')(default='', max_length=50))

        # Changing field 'StormDrain.species2'
        db.alter_column(u'storm_drain', 'species2', self.gf('django.db.models.fields.BooleanField')(default=None, max_length=10))

        # Changing field 'StormDrain.activity'
        db.alter_column(u'storm_drain', 'activity', self.gf('django.db.models.fields.BooleanField')(default=None, max_length=10))

        # Changing field 'StormDrain.date'
        db.alter_column(u'storm_drain', 'date', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'StormDrain.model'
        db.alter_column(u'storm_drain', 'model', self.gf('django.db.models.fields.CharField')(default='', max_length=5))

        # Changing field 'StormDrain.size'
        db.alter_column(u'storm_drain', 'size', self.gf('django.db.models.fields.CharField')(default='', max_length=5))

        # Changing field 'StormDrain.type'
        db.alter_column(u'storm_drain', 'type', self.gf('django.db.models.fields.CharField')(default='', max_length=100))

        # Changing field 'StormDrain.treatment'
        db.alter_column(u'storm_drain', 'treatment', self.gf('django.db.models.fields.BooleanField')(default=None, max_length=10))

    models = {
        u'tigapublic.authuser': {
            'Meta': {'object_name': 'AuthUser', 'db_table': "u'auth_user'", 'managed': 'False'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'tigapublic.mapauxreports': {
            'Meta': {'object_name': 'MapAuxReports', 'db_table': "u'map_aux_reports'", 'managed': 'False'},
            'dataset_license': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'edited_user_notes': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'expert_validated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'expert_validation_result': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'final_expert_status': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {}),
            'observation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'photo_license': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'photo_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'private_webmap_layer': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'ref_system': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            's_a_1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_a_2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_a_3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_a_4': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_q_1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_q_2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_q_3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            's_q_4': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'simplified_expert_validation_result': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'single_report_map_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'site_cat': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'storm_drain_status': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            't_a_1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            't_a_2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            't_a_3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            't_q_1': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            't_q_2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            't_q_3': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '7', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'version_uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'})
        },
        u'tigapublic.notification': {
            'Meta': {'object_name': 'Notification', 'db_table': "u'tigaserver_app_notification'", 'managed': 'False'},
            'acknowledged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_comment': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2017, 6, 14, 0, 0)'}),
            'expert': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"}),
            'expert_comment': ('django.db.models.fields.TextField', [], {}),
            'expert_html': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.NotificationContent']"}),
            'photo_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.MapAuxReports']", 'to_field': "u'version_uuid'"}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        u'tigapublic.notificationcontent': {
            'Meta': {'object_name': 'NotificationContent', 'db_table': "u'tigaserver_app_notificationcontent'", 'managed': 'False'},
            'body_html_ca': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'body_html_en': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'body_html_es': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title_ca': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title_en': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title_es': ('django.db.models.fields.TextField', [], {})
        },
        u'tigapublic.notificationimageformmodel': {
            'Meta': {'object_name': 'NotificationImageFormModel'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'})
        },
        u'tigapublic.stormdrain': {
            'Meta': {'object_name': 'StormDrain', 'db_table': "u'storm_drain'"},
            'activity': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2017, 6, 14, 0, 0)', 'null': 'True', 'blank': 'True'}),
            'icon': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '6'}),
            'lon': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '6'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'municipality': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'original_lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'original_lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'sand': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'species1': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'species2': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'treatment': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"}),
            'version': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'water': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        u'tigapublic.stormdrainuserversions': {
            'Meta': {'object_name': 'StormDrainUserVersions', 'db_table': "u'tigapublic_storm_drain_user_version'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'published_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2017, 6, 14, 0, 0)'}),
            'style_json': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"}),
            'version': ('django.db.models.fields.IntegerField', [], {}),
            'visible': ('django.db.models.fields.BooleanField', [], {})
        }
    }

    complete_apps = ['tigapublic']