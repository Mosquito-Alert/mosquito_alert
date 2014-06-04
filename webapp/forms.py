from django.forms.models import modelform_factory
from tigaserver_app.models import Report


ReportForm = modelform_factory(Report, fields=('type', 'location_choice'))