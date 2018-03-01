# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CrowdcraftingTask'
        db.create_table(u'tigacrafting_crowdcraftingtask', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task_id', self.gf('django.db.models.fields.IntegerField')(default=None, unique=True, null=True)),
            ('photo', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['tigaserver_app.Photo'], unique=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['CrowdcraftingTask'])

        # Adding model 'CrowdcraftingUser'
        db.create_table(u'tigacrafting_crowdcraftinguser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['CrowdcraftingUser'])

        # Adding model 'CrowdcraftingResponse'
        db.create_table(u'tigacrafting_crowdcraftingresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response_id', self.gf('django.db.models.fields.IntegerField')()),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['tigacrafting.CrowdcraftingTask'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='responses', null=True, to=orm['tigacrafting.CrowdcraftingUser'])),
            ('user_lang', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('mosquito_question_response', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('tiger_question_response', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('site_question_response', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('finish_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('user_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['CrowdcraftingResponse'])

        # Adding model 'Annotation'
        db.create_table(u'tigacrafting_annotation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='annotations', to=orm['auth.User'])),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='annotations', to=orm['tigacrafting.CrowdcraftingTask'])),
            ('tiger_certainty_percent', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('value_changed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), auto_now_add=True, blank=True)),
            ('working_on', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'tigacrafting', ['Annotation'])

        # Adding model 'MoveLabAnnotation'
        db.create_table(u'tigacrafting_movelabannotation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.OneToOneField')(related_name='movelab_annotation', unique=True, to=orm['tigacrafting.CrowdcraftingTask'])),
            ('tiger_certainty_category', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('certainty_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('hide', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('edited_user_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'tigacrafting', ['MoveLabAnnotation'])

        # Adding model 'ExpertReportAnnotation'
        db.create_table(u'tigacrafting_expertreportannotation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='expert_report_annotations', to=orm['auth.User'])),
            ('report', self.gf('django.db.models.fields.related.ForeignKey')(related_name='expert_report_annotations', to=orm['tigaserver_app.Report'])),
            ('tiger_certainty_category', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('aegypti_certainty_category', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('tiger_certainty_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('site_certainty_category', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
            ('site_certainty_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('edited_user_notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('message_for_user', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), auto_now=True, blank=True)),
            ('validation_complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('revise', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('best_photo', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='expert_report_annotations', null=True, to=orm['tigaserver_app.Photo'])),
            ('linked_id', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2018, 3, 1, 0, 0), auto_now_add=True, blank=True)),
            ('simplified_annotation', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'tigacrafting', ['ExpertReportAnnotation'])

        # Adding model 'UserStat'
        db.create_table(u'tigacrafting_userstat', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True, primary_key=True)),
            ('grabbed_reports', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'tigacrafting', ['UserStat'])


    def backwards(self, orm):
        # Deleting model 'CrowdcraftingTask'
        db.delete_table(u'tigacrafting_crowdcraftingtask')

        # Deleting model 'CrowdcraftingUser'
        db.delete_table(u'tigacrafting_crowdcraftinguser')

        # Deleting model 'CrowdcraftingResponse'
        db.delete_table(u'tigacrafting_crowdcraftingresponse')

        # Deleting model 'Annotation'
        db.delete_table(u'tigacrafting_annotation')

        # Deleting model 'MoveLabAnnotation'
        db.delete_table(u'tigacrafting_movelabannotation')

        # Deleting model 'ExpertReportAnnotation'
        db.delete_table(u'tigacrafting_expertreportannotation')

        # Deleting model 'UserStat'
        db.delete_table(u'tigacrafting_userstat')


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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
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
            'user_lang': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'tigacrafting.crowdcraftingtask': {
            'Meta': {'object_name': 'CrowdcraftingTask'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['tigaserver_app.Photo']", 'unique': 'True'}),
            'task_id': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'unique': 'True', 'null': 'True'})
        },
        u'tigacrafting.crowdcraftinguser': {
            'Meta': {'object_name': 'CrowdcraftingUser'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tigacrafting.expertreportannotation': {
            'Meta': {'object_name': 'ExpertReportAnnotation'},
            'aegypti_certainty_category': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'best_photo': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'expert_report_annotations'", 'null': 'True', 'to': u"orm['tigaserver_app.Photo']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'edited_user_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'linked_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'message_for_user': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'report': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expert_report_annotations'", 'to': u"orm['tigaserver_app.Report']"}),
            'revise': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'simplified_annotation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'site_certainty_category': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'site_certainty_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'tiger_certainty_category': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'tiger_certainty_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'expert_report_annotations'", 'to': u"orm['auth.User']"}),
            'validation_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'tigacrafting.movelabannotation': {
            'Meta': {'object_name': 'MoveLabAnnotation'},
            'certainty_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'auto_now_add': 'True', 'blank': 'True'}),
            'edited_user_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'hide': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2018, 3, 1, 0, 0)', 'auto_now': 'True', 'blank': 'True'}),
            'task': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'movelab_annotation'", 'unique': 'True', 'to': u"orm['tigacrafting.CrowdcraftingTask']"}),
            'tiger_certainty_category': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'tigacrafting.userstat': {
            'Meta': {'object_name': 'UserStat'},
            'grabbed_reports': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
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
            'uuid': ('django.db.models.fields.CharField', [], {'default': "'0280474a-827a-40c8-9521-86ed926bb936'", 'max_length': '36'})
        },
        u'tigaserver_app.report': {
            'Meta': {'unique_together': "(('user', 'version_UUID'),)", 'object_name': 'Report'},
            'app_language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
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
            'os_language': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'os_version': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'package_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '400', 'blank': 'True'}),
            'package_version': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'phone_upload_time': ('django.db.models.fields.DateTimeField', [], {}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
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
            'Meta': {'ordering': "('user_UUID',)", 'object_name': 'TigaUser'},
            'device_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'registration_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user_UUID': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'})
        }
    }

    complete_apps = ['tigacrafting']