# coding=utf-8
# !/usr/bin/env python
import os, sys

proj_path = os.path.abspath(os.path.dirname(__name__))
#proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from rest_framework.renderers import JSONRenderer
import json
from datetime import datetime
#import config
from tigaserver_project import settings
import psycopg2
from django.utils.dateparse import parse_datetime
from tigaserver_app.views import all_reports_internal
from tigaserver_app.views import get_cfa_reports, get_cfs_reports, non_visible_reports_internal, coverage_month_internal
from urllib.parse import urlsplit


def update_municipalities(cursor):
    cursor.execute(
        """SELECT r.version_uuid, muni.nombre FROM municipis_4326 muni,map_aux_reports r WHERE st_within(st_setsrid(st_point(r.lon,r.lat),4326),muni.geom)""")
    result = cursor.fetchall()
    for row in result:
        uuid = row[0]
        municipality = row[1]
        cursor.execute("""UPDATE map_aux_reports set municipality=%s WHERE version_uuid=%s;""",
                       (municipality, uuid,))

def update_tags(cursor):
    cursor.execute(
        """select a.report_id, t.slug from  taggit_taggeditem ti, taggit_tag t, tigacrafting_expertreportannotation a where ti.tag_id = t.id AND ti.object_id = a.id""")
    accumulated_tags = {}
    result = cursor.fetchall()
    for row in result:
        report_id = row[0]
        tag = row[1]
        tag_array = accumulated_tags.get(report_id,[])
        tag_array.append(tag)
        accumulated_tags[report_id] = tag_array
    for key in accumulated_tags.keys():
        tags = accumulated_tags[key]
        cursor.execute("""UPDATE map_aux_reports set tags=%s where version_uuid=%s;""",( str(tags),key ))


def update_user_uuids(cursor):
    cursor.execute(
        """UPDATE map_aux_reports m set user_id=(SELECT user_id from tigaserver_app_report r where m.version_uuid=r."version_UUID");""")


def update_report_ids(cursor):
    cursor.execute(
        """
        update map_aux_reports m set report_id=(select report_id from tigaserver_app_report r where m.version_uuid=r."version_UUID");
        """
    )

def move_hidden_adult_report_to_trash_layer(cursor):
    cursor.execute("""select "version_UUID" from tigaserver_app_report where hide=True and type='adult';""")
    result = cursor.fetchall()
    for row in result:
        uuid = row[0]
        cursor.execute("""UPDATE map_aux_reports set private_webmap_layer='trash_layer' WHERE version_uuid=%s;""",
                       (uuid,))


def add_photo_to_not_yet_filtered_adults(cursor):
    cursor.execute(
        """SELECT m.version_uuid,p.photo FROM map_aux_reports m,tigaserver_app_photo p WHERE p.report_id = m.version_uuid and private_webmap_layer='not_yet_validated' and n_photos > 0 and photo_url='' and p.hide=false;""")
    result = cursor.fetchall()
    last_uuid = '-1'
    for row in result:
        current_uuid = row[0]
        if current_uuid != last_uuid:
            # do stuff
            cursor.execute("""UPDATE map_aux_reports set photo_url=%s WHERE version_uuid=%s;""",
                           ('/media/' + row[1], row[0],))
        last_uuid = current_uuid;


def add_photo_to_unfiltered_sites(cursor):
    cursor.execute(
        """SELECT m.version_uuid,p.photo FROM map_aux_reports m,tigaserver_app_photo p WHERE p.report_id = m.version_uuid and ( private_webmap_layer='breeding_site_not_yet_filtered' or private_webmap_layer='storm_drain_water' or private_webmap_layer='storm_drain_dry' or private_webmap_layer='breeding_site_other' or private_webmap_layer='trash_layer') and n_photos > 0 and photo_url='' and p.hide=false;""")
    result = cursor.fetchall()
    last_uuid = '-1'
    for row in result:
        current_uuid = row[0]
        if current_uuid != last_uuid:
            # do stuff
            cursor.execute("""UPDATE map_aux_reports set photo_url=%s WHERE version_uuid=%s;""",
                           ('/media/' + row[1], row[0],))
        last_uuid = current_uuid;


def adjust_coarse_filter(cursor, file, webmap_layer):
    json_data = open(file)
    data = json.load(json_data)
    for bit in data:
        version_UUID = bit["version_UUID"]
        cursor.execute("""UPDATE map_aux_reports set private_webmap_layer=%s WHERE version_uuid=%s""",
                       (webmap_layer, version_UUID,))


def get_nota_usuari_de_report(cursor, version_UUID):
    cursor.execute("""SELECT note from tigaserver_app_report WHERE "version_UUID"=%s;""", (version_UUID,))
    result = cursor.fetchone()
    if not result is None and len(result) > 0:
        return result[0]
    return ''


def actualitza_nota_usuari(cursor, version_UUID, note):
    cursor.execute("""UPDATE map_aux_reports set note=%s WHERE version_uuid=%s;""", (note, version_UUID,))


def clean_photo_str(photo_str):
    if photo_str == '' or photo_str == 'None' or photo_str == None:
        return ''
    splitted_str = photo_str.split(' ')
    if len(splitted_str) > 0:
        str_href = splitted_str[1]
        str_href_nocomma = str_href.replace('"', '')
        str_clean = str_href_nocomma.replace('href=', '')
        return str_clean
    return ''


# 1
# "question": "Is it a storm drain or other type of breeding site?","question_id": 12
# "answer": "Storm drain", "answer_id": 121
# "answer": "Other breeding sites", "answer_id": 122

# 2
# "question": "Does it have water?", "question_id": 8
# "answer": "Yes", "answer_id": 101
# "answer": "No", "answer_id": 81
def get_storm_drain_status(report_responses):
    is_storm_drain = False
    water = False
    questions_have_id = False
    for report_response in report_responses:
        question_id = report_response.get('question_id',None)
        answer_id = report_response.get('answer_id', None)
        if question_id is not None and answer_id is not None:
            questions_have_id = True
            if question_id == 12 and answer_id == 121:
                is_storm_drain = True
            if question_id == 10 and answer_id == 101:
                water = True
        else:
            question = report_response['question']
            answer = report_response['answer']
            if question.startswith(u'Does it contain stagnant water') or question.startswith(u'Contiene agua estancada') or question.startswith(u'Cont\xe9 aigua estancada') or question.startswith(u'Does it have stagnant water') or question.startswith(u'\xbfContiene agua estancada') or question.startswith(u'Cont\xe9 aigua estancada'):
                if answer.startswith(u'Yes') or answer.startswith(u'S\xed') or answer.startswith(u'Has stagnant water') or answer.startswith(u'Hay agua') or answer.startswith(u'Hi ha aigua'):
                    return 'storm_drain_water'
                elif answer.startswith(u'No') or answer.startswith(u'Does not'):
                    return 'storm_drain_dry'
                else:
                    return 'other'
    if questions_have_id:
        if is_storm_drain and water:
            return 'storm_drain_water'
        elif is_storm_drain and not water:
            return 'storm_drain_dry'
        else:
            return 'other'
    return 'other'


this_year = datetime.now().year

# headers = {'Authorization': config.params['auth_token']}

#server_url = config.params['server_url']
#split_url = urlsplit(settings['STATIC_URL'])
#server_url = split_url.scheme + "//" + split_url.netloc
server_url = "https://webserver.mosquitoalert.com"
static_path = settings.BASE_DIR + settings.STATIC_ROOT + '/'

filenames = []

# #####################################################################################################
# This block should only be uncommented running the script locally and with pregenerated map data files
# #####################################################################################################

filenames.append(static_path + "all_reports2014.json")
filenames.append(static_path + "all_reports2015.json")
filenames.append(static_path + "all_reports2016.json")
filenames.append(static_path + "all_reports2017.json")
filenames.append(static_path + "all_reports2018.json")
filenames.append(static_path + "all_reports2019.json")
filenames.append(static_path + "all_reports2020.json")
filenames.append(static_path + "all_reports2021.json")
filenames.append(static_path + "all_reports2022.json")
filenames.append(static_path + "all_reports2023.json")
filenames.append(static_path + "all_reports2024.json")
filenames.append(static_path + "all_reports2025.json")
filenames.append("/tmp/hidden_reports2014.json")
filenames.append("/tmp/hidden_reports2015.json")
filenames.append("/tmp/hidden_reports2016.json")
filenames.append("/tmp/hidden_reports2017.json")
filenames.append("/tmp/hidden_reports2018.json")
filenames.append("/tmp/hidden_reports2019.json")
filenames.append("/tmp/hidden_reports2020.json")
filenames.append("/tmp/hidden_reports2021.json")
filenames.append("/tmp/hidden_reports2022.json")
filenames.append("/tmp/hidden_reports2023.json")
filenames.append("/tmp/hidden_reports2024.json")
filenames.append("/tmp/hidden_reports2025.json")


# FILE WRITING


cfa_data = get_cfa_reports()
file = "/tmp/cfa.json"
text_file = open(file, "w")
text_file.write(json.dumps(cfa_data))
text_file.close()
print ('Coarse filter adults complete')

cfs_data = get_cfs_reports()
file = "/tmp/cfs.json"
text_file = open(file, "w")
text_file.write(json.dumps(cfs_data))
text_file.close()
print ('Coarse filter sites complete')


# experimental paginated endpoint
# for year in range(2014, this_year + 1):
#     print (str(year))
#     d = all_reports_internal(year)
#     json_string = JSONRenderer().render(d)
#     data = json.loads(json_string)
#     accumulated_results = json.dumps(data)

#     file = static_path + "all_reports" + str(year) + ".json"
#     text_file = open(file, "w")
#     text_file.write(accumulated_results)
#     text_file.close()


for year in range(2014, this_year + 1):
    print (str(year))
    d = non_visible_reports_internal(year)
    json_string = JSONRenderer().render(d)
    data = json.loads(json_string)
    accumulated_results = json.dumps(data)

    file = "/tmp/hidden_reports" + str(year) + ".json"
    text_file = open(file, "w")
    text_file.write(accumulated_results)
    text_file.close()
    print (str(year) + ' complete')

print('Starting coverage month request')
d = coverage_month_internal()
json_string = JSONRenderer().render(d)
data = json.loads(json_string)
accumulated_results = json.dumps(data)
text_file = open(static_path + "coverage_month_data.json", "w")
text_file.write(accumulated_results)
text_file.close()


# END FILE WRITING


#conn_string = "host='" + config.params['db_host'] + "' dbname='" + config.params['db_name'] + "' user='" + \
#              config.params['db_user'] + "' password='" + config.params['db_password'] + "' port='" + \
#              config.params['db_port'] + "'"
print ("Connecting to database")
#conn = psycopg2.connect(conn_string)
#conn = psycopg2.connect(dbname=config.params['db_name'], user=config.params['db_user'], password=config.params['db_password'], port=config.params['db_port'], host=config.params['db_host'])
conn = psycopg2.connect(dbname=settings.DATABASES["default"]["NAME"], user=settings.DATABASES["default"]["USER"], password=settings.DATABASES["default"]["PASSWORD"], port=settings.DATABASES["default"]["PORT"], host=settings.DATABASES["default"]["HOST"])
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS map_aux_reports CASCADE;")
cursor.execute("CREATE TABLE map_aux_reports (id serial primary key,version_uuid character varying(36) UNIQUE, " \
               "observation_date timestamp with time zone,lon double precision,lat double precision,ref_system character varying(36)," \
               "type character varying(7),breeding_site_answers character varying(100),mosquito_answers character varying(100)," \
               "expert_validated boolean,expert_validation_result character varying(100),simplified_expert_validation_result character varying(100)," \
               "site_cat integer, storm_drain_status character varying(50),edited_user_notes character varying(4000), " \
               "photo_url character varying(255),photo_license character varying(100),dataset_license character varying(100), " \
               "single_report_map_url character varying(255), n_photos integer, visible boolean, final_expert_status integer, note text, " \
               "private_webmap_layer character varying(255), " \
               "t_q_1 character varying(255), t_q_2 character varying(255), t_q_3 character varying(255), " \
               "t_a_1 character varying(255), t_a_2 character varying(255), t_a_3 character varying(255), " \
               "s_q_1 character varying(255), s_q_2 character varying(255), s_q_3 character varying(255), s_q_4 character varying(255)," \
               "s_a_1 character varying(255), s_a_2 character varying(255), s_a_3 character varying(255), s_a_4 character varying(255)," \
               "user_id character varying(36)," \
               "municipality character varying(100)," \
               "responses_json character varying(4000)," \
               "tags character varying(4000)," \
               "report_id character varying(4)" \
               ");")
conn.commit()

# breeding site report - questions and answers

# 1
# "question": "Is it a storm drain or other type of breeding site?","question_id": 12
# "answer": "Storm drain", "answer_id": 121
# "answer": "Other breeding sites", "answer_id": 122

# 2
# "question": "Does it have water?", "question_id": 8
# "answer": "Yes", "answer_id": 101
# "answer": "No", "answer_id": 81

# mosquito report - questions and answers

# 1
# "question": "What kind of mosquito do you think it is?", "question_id": 6
# "answer": "Invasive Aedes", "answer_id": 61
# "answer": "Common mosquito", "answer_id": 62
# "answer": "Other", "answer_id": 63

# 2
# "question": "How does your mosquito look?", "question_id": 7
# "answer": "Thorax 1", "answer_id": 711
# "answer": "Thorax 2", "answer_id": 712
# "answer": "Thorax 3", "answer_id": 713
# "answer": "Thorax 4", "answer_id": 714
# "answer": "Abdomen 1", "answer_id": 721
# "answer": "Abdomen 2", "answer_id": 722
# "answer": "Abdomen 3", "answer_id": 723
# "answer": "Abdomen 4", "answer_id": 724
# "answer": "3d leg 1", "answer_id": 731
# "answer": "3d leg 2", "answer_id": 732
# "answer": "3d leg 3", "answer_id": 733
# "answer": "3d leg 4", "answer_id": 734

# key - slug / value - old category
class_translation_table = {
    'other-species': 'other_species',
    'aedes-albopictus' : 'albopictus',
    'aedes-aegypti': 'aegypti',
    'aedes-japonicus': 'japonicus',
    'aedes-koreicus': 'koreicus',
    'japonicus-koreicus':'japonicus_koreicus',
    'albopictus-cretinus':'albopictus_cretinus',
    'not-sure': 'not_sure',
    'unclassified': 'unclassified',
    'off-topic': 'unclassified',
    'culex-sp': 'culex',
    'conflict': 'conflict',
    'complex': 'complex'
}

#for year in range(2014, this_year+1):
for file in filenames:
    print ("Writing file %s  to database" % file)
    json_data = open(file)
    data = json.load(json_data)
    for bit in data:
        creation_date_str = bit['creation_time']
        creation_date = parse_datetime(creation_date_str)
        site_responses_str = ''
        tiger_responses_str = ''
        movelab_annotation_str = ''
        edited_user_notes = ''
        expert_validation_result = 'none#none'
        simplified_expert_validation_result = 'nosesabe'
        single_report_map_url = ''
        storm_drain_status = ''
        t_q_1, t_q_2, t_q_3 = '', '', ''
        tiger_questions = [t_q_1, t_q_2, t_q_3]
        t_a_1, t_a_2, t_a_3 = '', '', ''
        tiger_answers = [t_a_1, t_a_2, t_a_3]
        s_q_1, s_q_2, s_q_3, s_q_4 = '', '', '', ''
        site_questions = [s_q_1, s_q_2, s_q_3, s_q_4]
        s_a_1, s_a_2, s_a_3, s_a_4 = '', '', '', ''
        site_answers = [s_a_1, s_a_2, s_a_3, s_a_4]
        # new_storm_drain_status = ''
        photo_html_str = ''
        report_id = ''

        if bit['tiger_responses_text'] is not None:
            index_t = 0
            for key in bit['tiger_responses_text'].keys():
                try:
                    tiger_questions[index_t] = key
                    tiger_answers[index_t] = bit['tiger_responses_text'][key]
                except IndexError:
                    print("*** WARNING ***" + bit['version_UUID'])
                index_t = index_t + 1
        if bit['site_responses_text'] is not None:
            index_s = 0
            for key in bit['site_responses_text'].keys():
                try:
                    site_questions[index_s] = key
                    site_answers[index_s] = bit['site_responses_text'][key]
                except IndexError:
                    print("*** WARNING ***" + bit['version_UUID'])
                index_s = index_s + 1

        responses_json = bit['responses']

        validated = False
        if bit['movelab_annotation_euro'] != None and bit['movelab_annotation_euro'] and bit['movelab_annotation_euro'] != 'None' and bit['movelab_annotation_euro'] != '':
            validated = True
            if bit['type'] == 'adult':
                if file.find("2014") >= 0:
                    tiger_certainty_category = bit['movelab_annotation_euro'].get('tiger_certainty_category', 'not_value')
                    if tiger_certainty_category == 'not_value':
                        class_id = bit['movelab_annotation_euro'].get('class_id','-99')
                        if class_id == '99':
                            class_label = bit['movelab_annotation_euro'].get('class_label','no_label')
                            if class_label == 'no_label':
                                validated = False
                                expert_validation_result = 'unclassified#0'
                            elif class_label == 'conflict':
                                expert_validation_result = 'conflict#0'
                        else:
                            if class_id in [4,5,6,7,10]:
                                expert_validation_result = class_translation_table[bit['movelab_annotation_euro']['class_label']] + '#' + str(bit['movelab_annotation_euro']['class_value'])
                            else:
                                expert_validation_result = class_translation_table[bit['movelab_annotation_euro']['class_label']] + '#0'
                    else:
                        if bit['movelab_annotation_euro']['tiger_certainty_category'] != None and bit['movelab_annotation_euro']['tiger_certainty_category'] and bit['movelab_annotation_euro']['tiger_certainty_category'] != 'None' and bit['movelab_annotation_euro']['tiger_certainty_category'] != '':
                            if bit['movelab_annotation_euro']['tiger_certainty_category'] <= 0:
                                if bit['movelab_annotation_euro']['tiger_certainty_category'] < 0:
                                    expert_validation_result = 'other_species#0'
                                else:
                                    expert_validation_result = 'not_sure#0'
                            else:
                                expert_validation_result = 'albopictus#' + str(bit['movelab_annotation_euro']['tiger_certainty_category'])
                        else:
                            validated = False
                            expert_validation_result = 'unclassified#0'
                    try:
                        if bit['movelab_annotation_euro']['photo_html'] != None and bit['movelab_annotation_euro'][
                            'photo_html'] and bit['movelab_annotation_euro']['photo_html'] != 'None' and \
                                bit['movelab_annotation_euro']['photo_html'] != '':
                            photo_html_str = clean_photo_str(bit['movelab_annotation_euro']['photo_html'])
                    except KeyError:
                        pass
                else:
                    class_id = bit['movelab_annotation_euro'].get('class_id', '-99')
                    if class_id == '-99':
                        class_label = bit['movelab_annotation_euro'].get('class_label', 'no_label')
                        if class_label == 'no_label':
                            validated = False
                            expert_validation_result = 'unclassified#0'
                        elif class_label == 'conflict':
                            expert_validation_result = 'conflict#0'
                    else:
                        if bit['movelab_annotation_euro']['class_value'] is None:
                            expert_validation_result = class_translation_table[bit['movelab_annotation_euro']['class_label']] + '#0'
                        else:
                            expert_validation_result = class_translation_table[bit['movelab_annotation_euro']['class_label']] + '#' + str(bit['movelab_annotation_euro']['class_value'])
                    try:
                        if bit['movelab_annotation_euro']['photo_html'] != None and bit['movelab_annotation_euro'][
                            'photo_html'] and bit['movelab_annotation_euro']['photo_html'] != 'None' and \
                                bit['movelab_annotation_euro']['photo_html'] != '':
                            photo_html_str = clean_photo_str(bit['movelab_annotation_euro']['photo_html'])
                    except KeyError:
                        pass
                    '''
                    try:
                        expert_validation_result = bit['movelab_annotation_euro']['class_label'] + '#' + str(bit['movelab_annotation_euro']['class_value'])
                    except KeyError as e:
                        print(bit['movelab_annotation_euro'])
                        print(e)
                    '''
            elif bit['type'] == 'site':
                expert_validation_result = 'site#' + str(bit['movelab_annotation_euro']['site_certainty_category'])
                try:
                    if bit['movelab_annotation_euro']['photo_html'] != None and bit['movelab_annotation_euro']['photo_html'] and bit['movelab_annotation_euro']['photo_html'] != 'None' and bit['movelab_annotation_euro']['photo_html'] != '':
                        photo_html_str = clean_photo_str(bit['movelab_annotation_euro']['photo_html'])
                except KeyError:
                    pass
            elif bit['type'] == 'bite':
                expert_validation_result = 'bite#0'
            else:
                pass

            if bit['movelab_annotation']['edited_user_notes'] != None and bit['movelab_annotation']['edited_user_notes'] and bit['movelab_annotation']['edited_user_notes'] != 'None' and bit['movelab_annotation']['edited_user_notes'] != '':
                edited_user_notes = bit['movelab_annotation']['edited_user_notes']

        if bit['site_responses'] and bit['site_responses'] != 'None' and bit['site_responses'] != '':
            try:
                site_responses_str = str(bit['site_responses']['q1_response']) + '#' + str(
                    bit['site_responses']['q2_response'])
            except KeyError:
                pass
            try:
                site_responses_str = str(bit['site_responses']['q1_response_new']) + '#' + str(
                    bit['site_responses']['q2_response_new']) + '#' + str(bit['site_responses']['q3_response_new'])
            except KeyError:
                pass
        if bit['tiger_responses'] and bit['tiger_responses'] is not None and bit['tiger_responses'] != 'None' and bit[
            'tiger_responses'] != '':
            try:
                tiger_responses_str = str(bit['tiger_responses']['q1_response']) + '#' + str(
                    bit['tiger_responses']['q2_response']) + '#' + str(bit['tiger_responses']['q3_response'])
            except KeyError:
                print ("Error evaluating responses ")
                print (bit['tiger_responses'])
                tiger_responses_str = "0#0#" + str(bit['tiger_responses']['q3_response'])

        if expert_validation_result != '':
            expert_validation_prefix = expert_validation_result.split('#')[0]
            if expert_validation_prefix in ['albopictus','aegypti','japonicus','koreicus','japonicus-koreicus','albopictus-cretinus','culex','site','bite']:
                simplified_expert_validation_result = expert_validation_prefix
            elif expert_validation_prefix == 'other_species':
                simplified_expert_validation_result = 'noseparece'
            elif expert_validation_prefix in ['not_sure', 'unclassified']:
                simplified_expert_validation_result = 'nosesabe'
            elif expert_validation_prefix == 'conflict':
                simplified_expert_validation_result = 'conflict'

        if simplified_expert_validation_result != '' and simplified_expert_validation_result == 'site':
            if bit['site_cat'] != 0:
                storm_drain_status = 'other'
                simplified_expert_validation_result = simplified_expert_validation_result + "#" + storm_drain_status
            else:
                if len(responses_json) > 0:
                    storm_drain_status = get_storm_drain_status(responses_json)
                else:
                    storm_drain_status = 'other'

        single_report_map_url = server_url + '/es/single_report_map/' + bit['version_UUID']

        # kill conditions
        if bit['latest_version'] == True:
            try:
                cursor.execute(
                    """INSERT INTO map_aux_reports(version_uuid, observation_date,lon,lat,ref_system,type,breeding_site_answers,mosquito_answers,expert_validated,expert_validation_result,simplified_expert_validation_result,site_cat,storm_drain_status,edited_user_notes,photo_url,single_report_map_url,n_photos,visible,final_expert_status,t_q_1, t_q_2, t_q_3, t_a_1, t_a_2, t_a_3, s_q_1, s_q_2, s_q_3, s_q_4, s_a_1, s_a_2, s_a_3, s_a_4, responses_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
                    (bit['version_UUID'], creation_date, bit['lon'], bit['lat'], 'WGS84', bit['type'], site_responses_str,
                     tiger_responses_str, validated, expert_validation_result, simplified_expert_validation_result,
                     bit['site_cat'], storm_drain_status, edited_user_notes, photo_html_str, single_report_map_url,
                     bit['n_photos'], bit['visible'], bit['final_expert_status_text'], tiger_questions[0],
                     tiger_questions[1], tiger_questions[2], tiger_answers[0], tiger_answers[1], tiger_answers[2],
                     site_questions[0], site_questions[1], site_questions[2], site_questions[3], site_answers[0],
                     site_answers[1], site_answers[2], site_answers[3], json.dumps(responses_json)))
                note = get_nota_usuari_de_report(cursor, bit['version_UUID'])
                actualitza_nota_usuari(cursor, bit['version_UUID'], note)
                conn.commit()
            except:
                conn.rollback()


print ("Updating database")
# special points -> site#-4 are auto validated
cursor.execute(
    """UPDATE map_aux_reports set expert_validation_result = 'site#-4' where version_uuid in (select report_id from tigacrafting_expertreportannotation where site_certainty_notes='auto');""")
# end of special classification for 2014 sites

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='conflict' where expert_validation_result='conflict#0';""")

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='mosquito_tiger_confirmed' where type='adult' and expert_validated=True and expert_validation_result='albopictus#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='mosquito_tiger_probable' where type='adult' and expert_validated=True and expert_validation_result='albopictus#1' and n_photos > 0 and final_expert_status=1;""")

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='yellow_fever_confirmed' where type='adult' and expert_validated=True and expert_validation_result='aegypti#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='yellow_fever_probable' where type='adult' and expert_validated=True and expert_validation_result='aegypti#1' and n_photos > 0 and final_expert_status=1;""")

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='japonicus_confirmed' where type='adult' and expert_validated=True and expert_validation_result='japonicus#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='japonicus_probable' where type='adult' and expert_validated=True and expert_validation_result='japonicus#1' and n_photos > 0 and final_expert_status=1;""")

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='koreicus_confirmed' where type='adult' and expert_validated=True and expert_validation_result='koreicus#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='koreicus_probable' where type='adult' and expert_validated=True and expert_validation_result='koreicus#1' and n_photos > 0 and final_expert_status=1;""")

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='culex_confirmed' where type='adult' and expert_validated=True and expert_validation_result='culex#2' and n_photos > 0 and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='culex_probable' where type='adult' and expert_validated=True and expert_validation_result='culex#1' and n_photos > 0 and final_expert_status=1;""")

cursor.execute(
    #"""UPDATE map_aux_reports set private_webmap_layer='japonicus_koreicus' where type='adult' and expert_validated=True and expert_validation_result='japonicus-koreicus#0' and n_photos > 0 and final_expert_status=1;"""
    """UPDATE map_aux_reports set private_webmap_layer='japonicus_koreicus' where type='adult' and expert_validated=True and expert_validation_result='complex#1' and n_photos > 0 and final_expert_status=1;"""
)

cursor.execute(
    #"""UPDATE map_aux_reports set private_webmap_layer='albopictus_cretinus' where type='adult' and expert_validated=True and expert_validation_result='albopictus-cretinus#0' and n_photos > 0 and final_expert_status=1;"""
    """UPDATE map_aux_reports set private_webmap_layer='albopictus_cretinus' where type='adult' and expert_validated=True and expert_validation_result='complex#2' and n_photos > 0 and final_expert_status=1;"""
)

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='other_species' where type='adult' and expert_validated=True and (expert_validation_result='other_species#0') and n_photos > 0 and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='unidentified' where (type='adult' and n_photos = 0) or (type='adult' and expert_validated=True and expert_validation_result='not_sure#0' and n_photos > 0 and final_expert_status=1) or (type='adult' and expert_validated=False and expert_validation_result='none#none' and n_photos > 0 and final_expert_status=1);""")

cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validated=True and ( expert_validation_result='site#1' or expert_validation_result='site#2' or expert_validation_result='site#-4') and storm_drain_status='storm_drain_water'  and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validated=True and ( expert_validation_result='site#0' or expert_validation_result='site#-4') and storm_drain_status='storm_drain_dry' and final_expert_status=1;""")
# Move site#0 to breeding_site_other
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='breeding_site_other' where type='site' and expert_validated=True and ( expert_validation_result='site#0' or expert_validation_result='site#1' or expert_validation_result='site#2') and storm_drain_status='other' and final_expert_status=1;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='breeding_site_not_yet_filtered' where type='site' and expert_validated=False;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='trash_layer' where ( visible = False and final_expert_status<>0 ) or (expert_validated = True and (expert_validation_result='none#-3' or expert_validation_result='site#-3' or expert_validation_result='site#0' or expert_validation_result='none#none' or expert_validation_result='unclassified#0') and (final_expert_status = 1 or final_expert_status = -1)) or (type='site' and expert_validated=True and (expert_validation_result='site#-2' or expert_validation_result='site#-1') and final_expert_status = 0) or (type='site' and expert_validated=True and (expert_validation_result='site#-2' or expert_validation_result='site#-1') and final_expert_status = 1);""")
# visible set to false - if the reports have'nt been validated they won't be visible
# cursor.execute(
#    """UPDATE map_aux_reports set private_webmap_layer='not_yet_validated' where type='adult' and expert_validated=False and n_photos > 0 and visible=False;""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='not_yet_validated' where type='adult' and expert_validated=False and n_photos > 0;""")

# Move site#0 to breeding_site_other
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='breeding_site_other' where expert_validation_result = 'site#-4' and private_webmap_layer IS NULL;""")
# we remove unclassified points from 2014 -> go to trash_layer
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='trash_layer' where private_webmap_layer='not_yet_validated' and to_char(observation_date,'YYYY')='2014';""")
# Currently 3 points - in this case the user says it's a dry storm drain while the expert says there's water. We lean toward the expert
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where private_webmap_layer IS NULL and expert_validation_result = 'site#1';""")
# add photos to unfiltered sites. They don't have photo because there is no movelab_annotation
# special classification for 2014 sites
# 2014 auto-validated sites don't have movelab_annotation, therefore they are always labeled as expert_validated = false
# they have to be manually classified in storm drain (water/dry) and other manually
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and ((s_q_1 = 'Tipo de lugar de cría' or s_q_1 = 'Type of breeding site') and (((s_q_1 = 'Tipo de lugar de cría' or s_q_1 = 'Type of breeding site') and (s_a_1 = 'Sumideros' or s_a_1 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and (s_a_2 = 'Sí' or s_a_2 = 'Yes'))));""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (((s_q_1 = 'Tipo de lugar de cría' or s_q_1 = 'Type of breeding site') and (s_a_1 = 'Sumideros' or s_a_1 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and s_a_2 = 'No'));""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (((s_q_3 = 'Tipo de lugar de cría' or s_q_3 = 'Type of breeding site') and (s_a_3 = 'Sumideros' or s_a_3 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and (s_a_2 = 'Sí' or s_a_2 = 'Yes')));""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (((s_q_3 = 'Tipo de lugar de cría' or s_q_3 = 'Type of breeding site') and (s_a_3 = 'Sumideros' or s_a_3 = 'Storm drain')) or ((s_q_2 = '¿Contiene agua estancada?' or s_q_2 = 'Does it have stagnant water inside?') and s_a_2 = 'No'));""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_water' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (s_q_3 = 'Selecciona lloc de cria' and s_a_3 = 'Embornals' and s_q_1 = 'Conté aigua estancada?' and s_a_1 = 'Sí');""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='storm_drain_dry' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat = 0 and expert_validated = FALSE and (s_q_3 = 'Selecciona lloc de cria' and s_a_3 = 'Embornals' and s_q_1 = 'Conté aigua estancada?' and s_a_1 = 'No');""")
cursor.execute(
    """UPDATE map_aux_reports set private_webmap_layer='breeding_site_other' where type='site' and expert_validation_result = 'site#-4' and to_char(observation_date, 'YYYY') = '2014' and site_cat <> 0 and expert_validated = FALSE;""")
add_photo_to_unfiltered_sites(cursor)
add_photo_to_not_yet_filtered_adults(cursor)
move_hidden_adult_report_to_trash_layer(cursor)

#Added field municipality_id to table, petition by SIGTE
cursor.execute("""ALTER TABLE map_aux_reports add column municipality_id integer;""")
cursor.execute("""UPDATE map_aux_reports set municipality_id = foo.gid from ( SELECT r.version_uuid, muni.nombre, muni.gid FROM municipis_4326 muni,map_aux_reports r WHERE st_within(st_setsrid(st_point(r.lon,r.lat),4326),muni.geom)) as foo where foo.version_uuid = map_aux_reports.version_uuid;""")

print ("Adjusting coarse filter adults")
adjust_coarse_filter(cursor, "/tmp/cfa.json", "not_yet_validated")
print ("Adjusting coarse filter sites")
adjust_coarse_filter(cursor, "/tmp/cfs.json", "breeding_site_not_yet_filtered")

print ("Filling user ids")
update_user_uuids(cursor)

print ("Updating municipalities")
update_municipalities(cursor)

print ("Updating tags")
update_tags(cursor)

print ("Updating report_ids")
update_report_ids(cursor)

# regenerate map view (drop table destroys it)
print ("Regenerating views")

cursor.execute("""
CREATE MATERIALIZED VIEW public.reports_map_data AS 
 WITH validated_data AS (
         SELECT map_aux_reports.private_webmap_layer AS category,
            map_aux_reports.id,
            map_aux_reports.version_uuid,
            map_aux_reports.observation_date,
            map_aux_reports.lat,
            map_aux_reports.lon,
            map_aux_reports.expert_validation_result
           FROM map_aux_reports
          WHERE map_aux_reports.final_expert_status <> 0 AND map_aux_reports.lon IS NOT NULL AND map_aux_reports.lat IS NOT NULL AND map_aux_reports.lat <> '-1'::integer::double precision AND map_aux_reports.lon <> '-1'::integer::double precision
        )
 SELECT foo2.id,
    foo2.version_uuid,
    foo2.c,
    foo2.expert_validation_result,
    foo2.category,
    foo2.month,
    st_x(foo2.geom) AS lon,
    st_y(foo2.geom) AS lat,
    2 AS geohashlevel,
    st_setsrid(foo2.geom, 4326) AS geom
   FROM ( SELECT count(*) AS c,
            validated_data.category,
            validated_data.expert_validation_result,
            to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,
                CASE
                    WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326)
                    ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 2)))
                END AS geom,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer
                    ELSE NULL::integer
                END AS id,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.version_uuid::text, ','::text)::character varying
                    ELSE NULL::character varying
                END AS version_uuid
           FROM validated_data
          GROUP BY validated_data.category, (st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 2)), (to_char(validated_data.observation_date, 'YYYYMM'::text)), validated_data.expert_validation_result) foo2
UNION
 SELECT foo3.id,
    foo3.version_uuid,
    foo3.c,
    foo3.expert_validation_result,
    foo3.category,
    foo3.month,
    st_x(foo3.geom) AS lon,
    st_y(foo3.geom) AS lat,
    3 AS geohashlevel,
    st_setsrid(foo3.geom, 4326) AS geom
   FROM ( SELECT count(*) AS c,
            validated_data.category,
            validated_data.expert_validation_result,
            to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,
                CASE
                    WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326)
                    ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 3)))
                END AS geom,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer
                    ELSE NULL::integer
                END AS id,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.version_uuid::text, ','::text)::character varying
                    ELSE NULL::character varying
                END AS version_uuid
           FROM validated_data
          GROUP BY validated_data.category, (st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 3)), (to_char(validated_data.observation_date, 'YYYYMM'::text)), validated_data.expert_validation_result) foo3
UNION
 SELECT foo4.id,
    foo4.version_uuid,
    foo4.c,
    foo4.expert_validation_result,
    foo4.category,
    foo4.month,
    st_x(foo4.geom) AS lon,
    st_y(foo4.geom) AS lat,
    4 AS geohashlevel,
    st_setsrid(foo4.geom, 4326) AS geom
   FROM ( SELECT count(*) AS c,
            validated_data.category,
            validated_data.expert_validation_result,
            to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,
                CASE
                    WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326)
                    ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 4)))
                END AS geom,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer
                    ELSE NULL::integer
                END AS id,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.version_uuid::text, ','::text)::character varying
                    ELSE NULL::character varying
                END AS version_uuid
           FROM validated_data
          GROUP BY validated_data.category, (st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 4)), (to_char(validated_data.observation_date, 'YYYYMM'::text)), validated_data.expert_validation_result) foo4
UNION
 SELECT foo5.id,
    foo5.version_uuid,
    foo5.c,
    foo5.expert_validation_result,
    foo5.category,
    foo5.month,
    st_x(foo5.geom) AS lon,
    st_y(foo5.geom) AS lat,
    5 AS geohashlevel,
    st_setsrid(foo5.geom, 4326) AS geom
   FROM ( SELECT count(*) AS c,
            validated_data.category,
            validated_data.expert_validation_result,
            to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,
                CASE
                    WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326)
                    ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 5)))
                END AS geom,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer
                    ELSE NULL::integer
                END AS id,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.version_uuid::text, ','::text)::character varying
                    ELSE NULL::character varying
                END AS version_uuid
           FROM validated_data
          GROUP BY validated_data.category, (st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 5)), (to_char(validated_data.observation_date, 'YYYYMM'::text)), validated_data.expert_validation_result) foo5
UNION
 SELECT foo7.id,
    foo7.version_uuid,
    foo7.c,
    foo7.expert_validation_result,
    foo7.category,
    foo7.month,
    st_x(foo7.geom) AS lon,
    st_y(foo7.geom) AS lat,
    7 AS geohashlevel,
    st_setsrid(foo7.geom, 4326) AS geom
   FROM ( SELECT count(*) AS c,
            validated_data.category,
            validated_data.expert_validation_result,
            to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,
                CASE
                    WHEN count(*)::integer = 1 THEN st_setsrid(st_makepoint(min(validated_data.lon), min(validated_data.lat)), 4326)
                    ELSE st_centroid(st_geomfromgeohash(st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 7)))
                END AS geom,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.id::character varying::text, ','::text)::integer
                    ELSE NULL::integer
                END AS id,
                CASE
                    WHEN count(*)::integer = 1 THEN string_agg(validated_data.version_uuid::text, ','::text)::character varying
                    ELSE NULL::character varying
                END AS version_uuid
           FROM validated_data
          GROUP BY validated_data.category, (st_geohash(st_setsrid(st_makepoint(validated_data.lon, validated_data.lat), 4326), 7)), (to_char(validated_data.observation_date, 'YYYYMM'::text)), validated_data.expert_validation_result) foo7
UNION
 SELECT foo8.id,
    foo8.version_uuid,
    foo8.c,
    foo8.expert_validation_result,
    foo8.category,
    foo8.month,
    foo8.lon,
    foo8.lat,
    8 AS geohashlevel,
    st_setsrid(st_makepoint(foo8.lon, foo8.lat), 4326) AS geom
   FROM ( SELECT 1 AS c,
            validated_data.category,
            validated_data.expert_validation_result,
            to_char(validated_data.observation_date, 'YYYYMM'::text) AS month,
            validated_data.lon,
            validated_data.lat,
            validated_data.id,
            validated_data.version_uuid
           FROM validated_data) foo8
  ORDER BY 7
WITH DATA;
""")

conn.commit()

try:
    cursor.execute("""grant select on map_aux_reports to epidata;""")
    conn.commit()
except psycopg2.errors.UndefinedObject:
    conn.rollback()
try:
    cursor.execute("""grant select on map_aux_reports to culex;""")
    conn.commit()
except psycopg2.errors.UndefinedObject:
    conn.rollback()



cursor.close()
conn.close()