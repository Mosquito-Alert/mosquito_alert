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
import csv

def main():
    # buckets = {}

    reports = Report.objects.exclude( creation_time__year__in=[2014,2015,2016,2017,2018,2019])

    # for c in EuropeCountry.objects.all():
    #     if c.gid == 17:
    #         buckets['Spain/Other'] = {}
    #     else:
    #         buckets[str(c.name_engl)] = {}

    headers = (['country', 'report_short_id','report_long_id','species'])

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
                        validation_writer.writerow([country_name, r.report_id, r.version_UUID, str(ano.other_species)])
                        # if r.country is None or r.country.gid == 17:
                        #     try:
                        #         current_num = buckets['Spain/Other'][str(ano.other_species)]
                        #         buckets['Spain/Other'][str(ano.other_species)] = current_num + 1
                        #     except KeyError:
                        #         buckets['Spain/Other'][str(ano.other_species)] = 1
                        # else:
                        #     try:
                        #         current_num = buckets[str(r.country.name_engl)][str(ano.other_species)]
                        #         buckets[str(r.country.name_engl)][str(ano.other_species)] = current_num + 1
                        #     except KeyError:
                        #         buckets[str(r.country.name_engl)][str(ano.other_species)] = 1
            #bar.next()
    #bar.finish()

    # clean_buckets = {k: v for k, v in buckets.items() if v}
    #
    # headers = (['country','species','n'])
    # with open('/home/webuser/webapps/tigaserver/static/other_species_count.csv', mode='w') as validation_data:
    #     validation_writer = csv.writer(validation_data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #     validation_writer.writerow(headers)
    #     for info in clean_buckets.items():
    #         country = info[0]
    #         species = info[1]
    #         for k, v in species.items():
    #             validation_writer.writerow([country, k, v])

if __name__ == "__main__":
    main()
