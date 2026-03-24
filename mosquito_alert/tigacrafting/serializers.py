from rest_framework import serializers

from mosquito_alert.tigacrafting.models import Alert

class DataTableAimalertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ('xvb','report_id','report_datetime','loc_code','cat_id','species','certainty','status','hit','review_species','review_status','review_datetime')
