# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MoveLabAnnotation'
        db.create_table(u'tigacrafting_movelabannotation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.OneToOneField')(related_name='movelab_annotations', unique=True, to=orm['tigacrafting.CrowdcraftingTask'])),
            ('tiger_certainty_category', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('certainty_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('hide', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('edited_user_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 11, 12, 0, 0), auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2014, 11, 12, 0, 0), auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['MoveLabAnnotation'])


    def backwards(self, orm):
        # Deleting model 'MoveLabAnnotation'
        db.delete_table(u'tigacrafting_movelabannotation')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'tigacrafting.annotation': {
            'Meta': {'object_name': 'Annotation'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 11, 12, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 11, 12, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'annotations'", 'to': u"orm['tigacrafting.CrowdcraftingTask']"}),
            'tiger_certainty_percent': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'annotations'", 'to': u"orm['auth.User']"}),
            'value_changed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'working_on': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'tigacrafting.crowdcraftingresponse': {
            'Meta': {'object_name': 'CrowdcraftingResponse'},
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'finish_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mosquito_question_response': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'response_id': ('django.db.models.fields.IntegerField', [], {}),
            'site_question_response': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['tigacrafting.CrowdcraftingTask']"}),
            'tiger_question_response': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responses'", 'null': 'True', 'to': u"orm['tigacrafting.CrowdcraftingUser']"}),
            'user_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'user_lang': ('django.db.models.fields.CharField', [], {'max_length': '2', 'blank': 'True'})
        },
        u'tigacrafting.crowdcraftingtask': {
            'Meta': {'object_name': 'CrowdcraftingTask'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tigaserver_app.Photo']", 'unique': 'True'}),
            'task_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        u'tigacrafting.crowdcraftinguser': {
            'Meta': {'object_name': 'CrowdcraftingUser'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tigacrafting.movelabannotation': {
            'Meta': {'object_name': 'MoveLabAnnotation'},
            'certainty_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 11, 12, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'edited_user_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 11, 12, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'task': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'movelab_annotations'", 'unique': 'True', 'to': u"orm['tigacrafting.CrowdcraftingTask']"}),
            'tiger_certainty_category': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
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
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'photos'", 'to': u"orm['tigaserver_app.Report']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'5e49209f-3fc9-4fa8-88d3-62e1cfa16ff8'", 'max_length': '36'})
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