from tigaserver_app.models import ExpertReportAnnotation
from rest_framework import serializers


class ExpertReportAnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpertReportAnnotation
        fields = '__all__'