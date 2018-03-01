# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'NotificationImageFormModel'
        db.create_table(u'tigapublic_notificationimageformmodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
        ))
        db.send_create_signal(u'tigapublic', ['NotificationImageFormModel'])

        # Adding model 'MapAuxReports'
        db.create_table(u'map_aux_reports', (
            ('id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('version_uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36, blank=True)),
            ('user_id', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('observation_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('lon', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('ref_system', self.gf('django.db.models.fields.CharField')(max_length=36, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=7, blank=True)),
            ('t_q_1', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('t_a_1', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('t_q_2', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('t_a_2', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('t_q_3', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('t_a_3', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_q_1', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_a_1', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_q_2', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_a_2', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_q_3', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_a_3', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_q_4', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('s_a_4', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('expert_validated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('expert_validation_result', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('simplified_expert_validation_result', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('site_cat', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('storm_drain_status', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('edited_user_notes', self.gf('django.db.models.fields.CharField')(max_length=4000, blank=True)),
            ('photo_url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('photo_license', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('dataset_license', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('single_report_map_url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('private_webmap_layer', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('final_expert_status', self.gf('django.db.models.fields.IntegerField')()),
            ('note', self.gf('django.db.models.fields.TextField')()),
            ('municipality', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'tigapublic', ['MapAuxReports'])

        # Adding model 'StormDrain'
        db.create_table(u'storm_drain', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('icon', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('version', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('municipality', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('water', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True, blank=True)),
            ('sand', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True, blank=True)),
            ('treatment', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True, blank=True)),
            ('species2', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True, blank=True)),
            ('species1', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True, blank=True)),
            ('activity', self.gf('django.db.models.fields.NullBooleanField')(max_length=10, null=True, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('lon', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=6)),
            ('lat', self.gf('django.db.models.fields.DecimalField')(max_digits=9, decimal_places=6)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.AuthUser'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), null=True, blank=True)),
            ('original_lon', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('original_lat', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('model', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
        ))
        db.send_create_signal(u'tigapublic', ['StormDrain'])

        # Adding model 'NotificationPredefined'
        db.create_table(u'tigaserver_app_notificationpredefined', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.AuthUser'])),
            ('body_html_es', self.gf('django.db.models.fields.TextField')()),
            ('body_html_ca', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
            ('body_html_en', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
            ('title_es', self.gf('django.db.models.fields.TextField')()),
            ('title_ca', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
            ('title_en', self.gf('django.db.models.fields.TextField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'tigapublic', ['NotificationPredefined'])

        # Adding model 'ObservationNotifications'
        db.create_table(u'tigapublic_map_notification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.MapAuxReports'], to_field=u'version_uuid')),
            ('user_id', self.gf('django.db.models.fields.CharField')(max_length=36)),
            ('expert', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.AuthUser'])),
            ('date_comment', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('expert_comment', self.gf('django.db.models.fields.TextField')()),
            ('expert_html', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notification_content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.NotificationContent'])),
            ('preset_notification', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['tigapublic.NotificationPredefined'], null=True, blank=True)),
        ))
        db.send_create_signal(u'tigapublic', ['ObservationNotifications'])

        # Adding model 'StormDrainUserVersions'
        db.create_table(u'tigapublic_storm_drain_user_version', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.AuthUser'])),
            ('version', self.gf('django.db.models.fields.IntegerField')()),
            ('published_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0))),
            ('style_json', self.gf('django.db.models.fields.TextField')()),
            ('visible', self.gf('django.db.models.fields.BooleanField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'tigapublic', ['StormDrainUserVersions'])

        # Adding model 'Municipalities'
        db.create_table(u'municipis_4326', (
            ('gid', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('municipality_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('nombre', self.gf('django.db.models.fields.CharField')(max_length=254, blank=True)),
            ('tipo', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('pertenenci', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('codigoine', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('codprov', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('cod_ccaa', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
        ))
        db.send_create_signal(u'tigapublic', ['Municipalities'])

        # Adding model 'UserMunicipalities'
        db.create_table(u'tigapublic_user_municipalities', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.AuthUser'])),
            ('municipality', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['tigapublic.Municipalities'], to_field=u'municipality_id')),
        ))
        db.send_create_signal(u'tigapublic', ['UserMunicipalities'])


    def backwards(self, orm):
        # Deleting model 'NotificationImageFormModel'
        db.delete_table(u'tigapublic_notificationimageformmodel')

        # Deleting model 'MapAuxReports'
        db.delete_table(u'map_aux_reports')

        # Deleting model 'StormDrain'
        db.delete_table(u'storm_drain')

        # Deleting model 'NotificationPredefined'
        db.delete_table(u'tigaserver_app_notificationpredefined')

        # Deleting model 'ObservationNotifications'
        db.delete_table(u'tigapublic_map_notification')

        # Deleting model 'StormDrainUserVersions'
        db.delete_table(u'tigapublic_storm_drain_user_version')

        # Deleting model 'Municipalities'
        db.delete_table(u'municipis_4326')

        # Deleting model 'UserMunicipalities'
        db.delete_table(u'tigapublic_user_municipalities')


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
            'Meta': {'object_name': 'MapAuxReports', 'db_table': "u'map_aux_reports'"},
            'dataset_license': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'edited_user_notes': ('django.db.models.fields.CharField', [], {'max_length': '4000', 'blank': 'True'}),
            'expert_validated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'expert_validation_result': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'final_expert_status': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'lon': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'municipality': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
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
        u'tigapublic.municipalities': {
            'Meta': {'object_name': 'Municipalities', 'db_table': "u'municipis_4326'"},
            'cod_ccaa': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'codigoine': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'codprov': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'}),
            'gid': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipality_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'nombre': ('django.db.models.fields.CharField', [], {'max_length': '254', 'blank': 'True'}),
            'pertenenci': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'tipo': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'tigapublic.notification': {
            'Meta': {'object_name': 'Notification', 'db_table': "u'tigaserver_app_notification'", 'managed': 'False'},
            'acknowledged': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_comment': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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
        u'tigapublic.notificationpredefined': {
            'Meta': {'object_name': 'NotificationPredefined', 'db_table': "u'tigaserver_app_notificationpredefined'"},
            'body_html_ca': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'body_html_en': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'body_html_es': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title_ca': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title_en': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'title_es': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"})
        },
        u'tigapublic.observationnotifications': {
            'Meta': {'object_name': 'ObservationNotifications', 'db_table': "u'tigapublic_map_notification'"},
            'date_comment': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'expert': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"}),
            'expert_comment': ('django.db.models.fields.TextField', [], {}),
            'expert_html': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_content': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.NotificationContent']"}),
            'preset_notification': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['tigapublic.NotificationPredefined']", 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.MapAuxReports']", 'to_field': "u'version_uuid'"}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '36'})
        },
        u'tigapublic.stormdrain': {
            'Meta': {'object_name': 'StormDrain', 'db_table': "u'storm_drain'"},
            'activity': ('django.db.models.fields.NullBooleanField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'null': 'True', 'blank': 'True'}),
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
        u'tigapublic.stormdrainrepresentation': {
            'Meta': {'object_name': 'StormDrainRepresentation', 'db_table': "u'tigapublic_storm_drain_representation'", 'managed': 'False'},
            'condition': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'operator': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '36'}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        u'tigapublic.stormdrainuserversions': {
            'Meta': {'object_name': 'StormDrainUserVersions', 'db_table': "u'tigapublic_storm_drain_user_version'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'published_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)'}),
            'style_json': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"}),
            'version': ('django.db.models.fields.IntegerField', [], {}),
            'visible': ('django.db.models.fields.BooleanField', [], {})
        },
        u'tigapublic.usermunicipalities': {
            'Meta': {'object_name': 'UserMunicipalities', 'db_table': "u'tigapublic_user_municipalities'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'municipality': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.Municipalities']", 'to_field': "u'municipality_id'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigapublic.AuthUser']"})
        }
    }

    complete_apps = ['tigapublic']