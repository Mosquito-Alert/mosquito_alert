import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from django.db import connection
import csv

ALL_YEARS = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]
OUT_FILE = 'presence_municipality_by_year.csv'

def main():
    with connection.cursor() as cursor:
        years_hash = {}
        cursor.execute('''
             select distinct extract('year' from mar.observation_date), m.nombre, m.codigoine
             from
             map_aux_reports mar ,
             municipis_4326 m
             where mar.municipality_id = m.gid and private_webmap_layer in ('mosquito_tiger_confirmed','mosquito_tiger_probable') and m.nombre is not null and m.codprov is not null
        ''')
        results = cursor.fetchall()
        for r in results:
            try:
                years_hash[r[2]]
            except KeyError:
                years_hash[r[2]] = []
            years_hash[r[2]].append(int(r[0]))

        cursor.execute('''
            select c.cod_ccaa , c.nom_ccaa,  m.codprov, p.nomprov , m.codigoine, m.nombre
            from municipis_4326 m ,
            provincies_4326 p ,
            comunitats_4326 c
            where m.codprov = p.codprov and
            m.cod_ccaa = c.cod_ccaa and
            codigoine like 'ES_%' order by 1,3,5
        ''')
        results = cursor.fetchall()
        with open(OUT_FILE, 'w') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(['cod_ccaa','nom_ccaa','cod_prov','nom_prov','codi_ine','nom_muni','pres_2014','pres_2015','pres_2016','pres_2017','pres_2018','pres_2019','pres_2020','pres_2021','pres_2022'])
            for row in results:
                processed_line = []
                for column in row:
                    processed_line.append(column)
                for year in ALL_YEARS:
                    try:
                        presence_year = years_hash[processed_line[4]]
                    except KeyError:
                        presence_year = []
                    if year in presence_year:
                        processed_line.append(str(year))
                    else:
                        processed_line.append("")
                csvwriter.writerow(processed_line)

if __name__ == '__main__':
    main()