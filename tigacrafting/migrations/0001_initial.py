# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CrowdcraftingTask'
        db.create_table(u'tigacrafting_crowdcraftingtask', (
            ('task_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('photo', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tigaserver_app.Photo'], unique=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['CrowdcraftingTask'])

        # Adding model 'CrowdcraftingUser'
        db.create_table(u'tigacrafting_crowdcraftinguser', (
            ('user_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['CrowdcraftingUser'])

        # Adding model 'CrowdcraftingResponse'
        db.create_table(u'tigacrafting_crowdcraftingresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['tigacrafting.CrowdcraftingTask'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['tigacrafting.CrowdcraftingUser'])),
            ('user_lang', self.gf('django.db.models.fields.CharField')(max_length=2, blank=True)),
            ('mosquito_question_response', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('tiger_question_response', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('site_question_response', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('finish_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('user_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
        ))
        db.send_create_signal(u'tigacrafting', ['CrowdcraftingResponse'])


    def backwards(self, orm):
        # Deleting model 'CrowdcraftingTask'
        db.delete_table(u'tigacrafting_crowdcraftingtask')

        # Deleting model 'CrowdcraftingUser'
        db.delete_table(u'tigacrafting_crowdcraftinguser')

        # Deleting model 'CrowdcraftingResponse'
        db.delete_table(u'tigacrafting_crowdcraftingresponse')


    models = {
        u'tigacrafting.crowdcraftingresponse': {
            'Meta': {'object_name': 'CrowdcraftingResponse'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'finish_time': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mosquito_question_response': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'site_question_response': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['tigacrafting.CrowdcraftingTask']"}),
            'tiger_question_response': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['tigacrafting.CrowdcraftingUser']"}),
            'user_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'user_lang': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'})
        },
        u'tigacrafting.crowdcraftingtask': {
            'Meta': {'object_name': 'CrowdcraftingTask'},
            'photo': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tigaserver_app.Photo']", 'unique': 'True'}),
            'task_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
        },
        u'tigacrafting.crowdcraftinguser': {
            'Meta': {'object_name': 'CrowdcraftingUser'},
            'user_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'})
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
        u'tigaserver_app.photo': {
            'Meta': {'object_name': 'Photo'},
            'hide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigaserver_app.Report']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'7046a9c3-ba6e-46ee-bb4f-c37d2cff7d5b'", 'max_length': '36'})
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
        u'tigaserver_app.tigauser': {
            'Meta': {'object_name': 'TigaUser'},
            'registration_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_UUID': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'})
        }
    }

    complete_apps = ['tigacrafting']