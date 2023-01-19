import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from tigacrafting.models import ExpertReportAnnotation
from tigaserver_app.models import Report
import csv

def main():

    reports = Report.objects.exclude( creation_time__year__in=[2014,2015,2016,2017,2018,2019])
    
    headers = (['country', 'report_short_id','species'])

    with open('/home/webuser/webapps/tigaserver/static/other_species_count.csv', mode='w') as validation_data:
        validation_writer = csv.writer(validation_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        validation_writer.writerow(headers)
        for r in reports:
            validation_struct = r.get_final_combined_expert_category_euro_struct()
            if validation_struct['category'] is not None and validation_struct['category'].id == 2:
                annots = ExpertReportAnnotation.objects.filter(report=r,user__groups__name='expert',validation_complete=True)
                for ano in annots:
                    if ano.other_species is not None:
                        country_name = 'Spain/Other' if r.country is None or r.country.gid == 17 else r.country.name_engl
                        validation_writer.writerow([country_name, r.report_id, str(ano.other_species)])


if __name__ == "__main__":
    main()
