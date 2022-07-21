from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from tigaserver_app.models import Report


@registry.register_document
class ReportDocument(Document):

    #latest_version = fields.BooleanField(attr='latest_version')
    #movelab_annotation = fields.ObjectField(attr='get_movelab_annotation_euro')

    class Index:
        name = 'reports'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Report

        fields = [
            'creation_time',
            'type',
            'version_number',
            'note'
        ]
