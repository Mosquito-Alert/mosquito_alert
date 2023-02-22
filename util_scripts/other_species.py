import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
from django.db.models import Q

application = get_wsgi_application()

from tigacrafting.models import ExpertReportAnnotation, Categories
from tigaserver_app.models import Report, EuropeCountry
#from progress.bar import Bar
import csv


def main():
    reports = Report.objects.exclude( creation_time__year__in=[2014,2015,2016,2017,2018,2019]).filter(type='adult')
    total = len(reports)
    headers = (['report_short_id', 'observation_date', 'report_long_id', 'species'])
    with open('/home/webuser/webapps/tigaserver/static/other_species.csv', mode='w') as validation_data:
        validation_writer = csv.writer(validation_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        validation_writer.writerow(headers)
        i = 1
        for r in reports:
            validation_struct = r.get_final_combined_expert_category_euro_struct()
            if validation_struct['category'] is not None and validation_struct['category'].id == 2:
                annots = ExpertReportAnnotation.objects.filter(report=r,user__groups__name='expert',validation_complete=True)
                for ano in annots:
                    if ano.other_species is not None:
                        validation_writer.writerow([r.report_id, r.creation_time, r.version_UUID, str(ano.other_species)])
                print("Done {0} of {1}".format( i, total ))
                i = i + 1


if __name__ == "__main__":
    main()