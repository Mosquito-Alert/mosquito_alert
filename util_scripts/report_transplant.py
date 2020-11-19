import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
from django.db.models import Q

application = get_wsgi_application()

from tigacrafting.models import ExpertReportAnnotation, Categories
from tigaserver_app.models import Report
import json

# ./manage.py dumpdata tigaserver_app.Report > all_reports.json
# ./manage.py dumpdata tigaserver_app.ReportResponse > all_reportresponses.json
# ./manage.py dumpdata tigacrafting.ExpertReportAnnotation > all_expertreportannotation.json
# ./manage.py dumpdata tigaserver_app.Photo > all_photos.json

IMAGINARY_USER_UUID = '15dde966-19ca-11eb-bc13-c85b76d93ea4'

def read_json_file_and_write_filtered(origin_file, destiny_file, filter_function,filter_list,substitution_function):
    f = open(origin_file, "r")
    file = f.read()
    json_file = json.loads(file)
    filtered_elems = []
    for elem in json_file:
        if filter_function(elem,filter_list) == True:
            subst_elem = substitution_function(elem)
            filtered_elems.append(subst_elem)
    filtered_string = json.dumps(filtered_elems)
    f = open(destiny_file, "w")
    f.write(filtered_string)
    f.close()


def report_filter_element_in_list(elem,list):
    if elem['pk'] in list:
        return True
    return False


def response_filter_element_in_list(elem,list):
    if elem['fields']['report'] in list:
        return True
    return False


def response_filter_element_in_list_and_exclude_zivko(elem,list):
    if elem['fields']['report'] in list:
        if elem['fields']['user'] != 148:
            return True
    return False


def report_replacer(elem):
    elem['fields']['user'] = IMAGINARY_USER_UUID
    return elem


def null_replacer(elem):
    return elem


def photo_compress_generator(photos_file, out_file):
    f = open(photos_file, "r")
    file = f.read()
    json_file = json.loads(file)
    command_line = "tar zcvf photos.tar.gz "
    photo_list = ""
    for elem in json_file:
        photo_list += elem['fields']['photo'].replace("tigapics/","") + " "
    command_line += photo_list
    f = open(out_file, "w")
    f.write(command_line)
    f.close()


def report_links_generator(report_file, out_file):
    f = open(report_file, "r")
    file = f.read()
    json_file = json.loads(file)
    fo = open(out_file, "w")
    for elem in json_file:
        fo.write("http://madev.creaf.cat/en/experts/status/reports/?version_uuid=" + elem['pk'] + "\n")
    fo.close()
    f.close()


def get_uuid_of_all_production_reports():
    f = open("all_production_reports.json", "r")
    file = f.read()
    json_file = json.loads(file)
    f.close()
    uuids = []
    for elem in json_file:
        uuids.append(elem['pk'])
    return uuids;


def generate_dump_files(country_id, report_type, reports_in_production):
    if country_id == 17:
        target_reports = Report.objects.filter(Q(country_id=country_id) | Q(country_id__isnull=True)).filter(creation_time__year=2020).filter(type=report_type).exclude(photos__isnull=True).exclude(version_UUID__in=reports_in_production).exclude(hide=True)
    else:
        target_reports = Report.objects.filter(country_id=country_id).filter(creation_time__year=2020).filter(type=report_type).exclude(photos__isnull=True).exclude(version_UUID__in=reports_in_production).exclude(hide=True)
    target_reports_uuid = target_reports.values("version_UUID")
    uuids = [r_v['version_UUID'] for r_v in target_reports_uuid]

    out_reports = "some_" + report_type + "_reports_" + str(country_id) + ".json"
    out_reportresponses = "some_" + report_type + "_reportresponses_" + str(country_id) + ".json"
    if report_type == 'adult':
        out_expertreportannotations = "some_" + report_type + "_expertreportannotation_" + str(country_id) + ".json"
    out_photos = "some_" + report_type + "_photos_" + str(country_id) + ".json"
    out_photo_script = "some_" + report_type + "_photos_" + str(country_id) + ".script"
    out_links_file = "some_" + report_type + "_links_" + str(country_id) + ".txt"

    read_json_file_and_write_filtered("all_reports.json", out_reports, report_filter_element_in_list, uuids, report_replacer)
    read_json_file_and_write_filtered("all_reportresponses.json", out_reportresponses, response_filter_element_in_list, uuids, null_replacer)
    if report_type == 'adult':
        read_json_file_and_write_filtered("all_expertreportannotation.json", out_expertreportannotations, response_filter_element_in_list_and_exclude_zivko, uuids, null_replacer)
    read_json_file_and_write_filtered("all_photos.json", out_photos, response_filter_element_in_list, uuids, null_replacer)
    photo_compress_generator(out_photos, out_photo_script)
    report_links_generator(out_reports,out_links_file)


def work():
    country_ids = [
        32,  # Albania
        34,  # Austria
        2,  # Belgium
        3,  # Bulgaria
        38,  # Croatia
        4,  # Cyprus
        20,  # Finland
        7,  # Germany
        16,  # Greece
        39,  # Hungary
        49,  # Italy
        36,  # Luxembourg
        6,  # Netherlands
        46,  # North Macedonia
        15,  # Portugal
        18,  # Romania
        19,  # Serbia
        12,  # Slovakia
        26,  # Slovenia
        17,  # Spain
        47,  # Switzerland
        21,  # Turkey
        29  # UK
    ]
    reports_already_in_production = get_uuid_of_all_production_reports()
    #these are site reports which are obviously fake or tests
    exclude_also = [
        '4f10a658-e071-464d-a615-e244b62bc028',
        '24971c3d-b1aa-4094-8e31-59b86da0ab6f',
        '5a1ec219-10c7-4ee5-b048-539299b60564',
        'a4414819-fbc7-44c4-a0fb-ef09c5748a23',
        '60d2adf6-0ef9-46b6-ab2d-b6aabea7f0fb',
        '8b0536af-e27e-40bb-8b90-41ed98b8908c',
        'afb53d2f-994b-4b95-908e-dbfdde88ffce',
        '2b16b3c7-2ce2-4a60-8089-ead5d600530f',
        'c97868f4-228d-4ae9-bab1-b950225872eb',
        '031d98ec-3abf-4fb4-919c-4de6847554f3',
        '06f82587-7a89-422a-a77d-dc8d1f40b5f2',
        '0cf24895-95a7-4250-9974-533b031ab957',
        '10ddcfda-5844-4c58-8ef5-82d969f53b29',
        '1482ddeb-e02b-419e-869c-fefcc3c08a48',
        '1a519bb2-2577-4a9b-ba30-931b16035428',
        '200ee99b-b74c-49c0-9664-58a7442740b8',
        '253160c1-473f-49af-b50a-c73fb8a2c502',
        '27b46437-ade5-4028-951c-23996688ec17',
        '29074c7c-276c-4ee9-89f8-aac86dd7743f',
        '2adf8f10-45bd-47f6-aba0-e49316349d57',
        '2bdc7f8c-1c4e-4feb-9a43-2a7c92e22fc6',
        '2e379327-b86b-4212-ab74-ed9659fca1bc',
        '327565cb-5e48-434a-9b81-10abbcc0a36a',
        '3451fb53-982b-4359-9377-3b9946a9f7c4',
        '35dacaeb-e60e-4aec-a173-35f75f62bacf',
        '37235f34-5fd9-42b6-814a-1967b9b50fc2',
        '37fc2bec-9751-42f5-bf9f-34fe8b7b6ce2',
        '40922664-7d04-413d-aef1-69062b938c8c',
        '427ad013-22f6-4b38-b722-2e3a8f39eeb0',
        '456b3fdd-5318-4803-88db-7ddb160898e5',
        '4e89fd8f-b787-4e8c-bddb-318160934e2d',
        '5bf11187-2e96-4443-97e0-ef28b801fcdf',
        '5cbd26af-34fe-4e65-929e-59582b051492',
        '6386cd1a-818f-4de2-8f02-a07661567498',
        '64311065-e879-47f0-b2f7-5b6a9ef602e3',
        '6441883f-1f34-4044-a061-03db0cf92817',
        '6b31d760-3e06-4be0-940d-4390c13f4e34',
        '6c35cc2f-51a0-42c0-ab1b-8c13ad221b97',
        '6c3cb02c-3cb0-4bce-ad6a-7c8b0b763924',
        '6cc7440d-be6e-4fb1-9b09-fd1fbe861833',
        '6de6f4be-6c36-43ca-8d95-b37ace529055',
        '77d95c07-307d-48d5-89dc-33f940e1d6bf',
        '7bf905bf-27de-47e1-957d-981c02cba9aa',
        '7f590b59-904e-4079-8009-99388f578ffe',
        '82ef5770-9a02-40e9-81bc-60cece09fd78',
        '8d3dd8ab-75e4-43f2-8e7c-8bea4fdb9aae',
        '96cc448b-8828-4fa4-88ea-06fe23d778fa',
        '978fc6d4-2369-46f0-9de4-eb03ad44dbc0',
        '9d9d00e7-0586-4ef6-a560-516d4ab226ac',
        '9db1b2a4-fda0-4d37-b437-d0cd9278bea8',
        '9dbb07ea-60c9-4499-9cae-7e834b11d933',
        'a05d3de9-19da-40c1-9ad7-0e8dca4d1274',
        'a5f0ddb5-2339-4e65-ae48-1a5a10196615',
        'a6a5489e-4523-4898-af0e-62bb42c6ec4a',
        'abf61db4-0f90-42a9-b0d1-17c12ad7fa06',
        'b15b27f8-9d94-4650-a338-8e79c0839294',
        'bed91e5e-8903-4048-8307-a286937cac14',
        'ce3482d4-846d-4d54-bf24-0f5d2421a735',
        'ced677e8-660e-43c1-b792-c4d3411e257f',
        'cf0134ce-9631-418e-8415-5fd44f592eeb',
        'd7acd82a-f3d4-43d3-9ec4-92a9aa206dec',
        'd94e0364-c04d-469b-b53d-820bc20ada5d',
        'dd7cb79f-98a6-48e1-b8be-03046f595480',
        'e36674cb-461d-460a-8bcd-e64d050f240f',
        'e5e388a6-b31a-4454-8ff2-d13f2d4d6fda',
        'e6e2663a-e75b-478b-bad4-a6ef5544d0cf',
        'f0319948-d087-4f96-b40f-4a7affbba193',
        'f2fc7a0d-ec56-4839-9793-1ea5913e3b73',
        'f3c2b3ef-078f-4379-b57a-d4c5a6719afc',
        'f49c3f26-28ce-4b6c-a161-e5d32cf6259c',
        'f52a61b1-8e01-484a-8a4c-cc88558c43be',
        'f6180578-ad4b-4ffa-860d-76bd11d2db80',
        '0c28f979-1940-43cd-bb11-d5b314eff00b',
        '11e09afd-7e92-494e-9933-70df7a085d7b',
        '14aba450-c224-47a3-b4d6-92450ea79d3f',
        '1efe8c0b-d50f-44ed-996c-052e7b262404',
        '28d0b98a-ad50-4d09-94fb-bde9389bf585',
        '2c477817-48e5-494e-9ccb-2fb3edfd2646',
        '2eb166a8-1094-4d6e-bb5d-36d8965db5fb',
        '3085716b-cded-436e-abdd-b05677f0ec0d',
        '34ad8fde-851a-40a5-92dd-42ccd039c405',
        '38ae77de-73ae-4472-a38c-87b30418333a',
        '3ad9038c-1bbc-40fc-a1d2-a757d6953be6',
        '3b27d1b5-fabd-42bc-a361-3d6c1189f292',
        '3d5874bd-4297-4640-86a8-d16f78158886',
        '3e810b2a-501c-4377-826b-e460db771dd2',
        '3fb9a6b9-56d0-40a8-a98e-da74f6e28404',
        '40083dba-8270-43df-a1c9-ffe8439425c3',
        '418a1f82-c586-444c-a747-fa1ee9508fa4',
        '45ddd2b2-6ce7-415b-a255-27f78fd23c6a',
        '4ee68a6a-2282-4deb-bab7-fbcb8dc5b667',
        '506ac55c-6fd6-4ed9-9c2a-34f25fe95c6f',
        '54d2fbc9-b308-43a5-aacb-8440917eec4d',
        '57176e9a-8b28-4926-9428-bd8553539aec',
        '5fa9bcd5-7a3d-484a-bf78-f704debe310c',
        '64b0983b-4c31-4a02-bdfe-0bdddf654627',
        '6feb50ba-2bb3-40ee-8081-d98b9ba71702',
        '73f18a89-8209-4560-8da3-34984bb351d3',
        '7ac55ca4-d6bf-4288-93c5-0f2510368ec8',
        '7f3f58e0-0c35-4996-a814-07bb733b009e',
        '8111bb98-dd51-44e6-897a-9d28c75fb16b',
        '880d0907-24de-40a4-b3eb-992b85251b20',
        '8e430ea2-a016-44ab-b32a-3e8fbf39608d',
        '906fc5cb-a692-404a-b706-3ac91fd721cf',
        '91f815ac-8f06-4b5e-aa02-5493d13fe7e3',
        '942959cd-1fb9-4c37-be80-6f5abcf5f017',
        'a2304321-596f-4dd3-872f-707a738139d1',
        'ad7bd0e3-8a7f-498c-bf56-158c953aa0d0',
        'adc28a64-b248-4f41-8341-2f9b2474f573',
        'b0d16174-c1f1-44c3-8d40-22cddb6a6c81',
        'b745c5fb-4f98-4da5-9614-1ce4f463101f',
        'bb20cf32-6683-4a84-a3ec-9575f0666079',
        'bcba3a85-0a65-4820-b636-bcfb4a321d06',
        'bdf1b173-bcf2-4215-8e6c-1d4aefd9b087',
        'c6028fe6-33e1-4bcf-8d9d-22a917572ecf',
        'c60b2e47-fc55-4180-aa75-4b2badf563e8',
        'cb92d7f3-d85a-403a-b2d9-8b9e1080184f',
        'cca28047-ef7e-42de-9006-f7195a636c45',
        'cd3fa158-8c5e-410a-be06-a2705cb3546b',
        'd263dbe5-03e1-4425-92f6-dfa51c5bd050',
        'd8b5ab7b-2108-4c2e-a5e2-4308949470ec',
        'da733a8c-fdb3-40dd-bcea-72ef947244b7',
        'db3ce59d-79d2-4413-be72-32dab6ad0412',
        'e699dc23-26d5-41db-85ba-06fab273d258',
        'eb41cb5e-f729-4fe0-a1aa-4ca5896dbe27',
        'ec34de68-6107-4d81-adcd-0fea0c394aea',
        'ec93b085-e5aa-4b70-90f7-dc5fe61a085d',
        'ed7b40e5-65c2-433b-8467-a9d47c61824f',
        'ed8f5931-3e46-452c-9c1f-8cefe8739037',
        'f24fb6f2-3b28-43fa-bdd0-681644027df0',
        'f357644c-51c8-45c6-9eb7-b4cb70bc78e3',
        'f3f964b0-3a24-4522-8e95-d5840f53c41e',
        'f9cbc4a1-193d-4124-b92c-38a12a1e4524',
        '77d8b481-2f3e-43a0-bc2a-7d444d585ca0',
        '84156b3c-ebd3-47bd-bfb7-b5d3bf49353d',
        'ac1f361d-1c3e-4e81-baea-9dcd8d7ee0be',
        'd2a876bc-5598-40af-8b1c-9f958a49af92',
        'de1ef9c8-e3b9-420a-9781-bb148a71035e',
        'c0627076-030b-4b8d-8c07-3f68d44d8919',
        '4ae1661f-d363-4433-b4e3-b41e7c07f9d8',
        '684e9a3e-955c-48b2-ae98-1307c28f3625',
        '2587ad9d-efba-4eef-bc3c-5f89028d57af',
        '19c8c779-5173-471b-9230-5cd6bcbda403',
        '0a038d75-3b29-413e-aeb4-efa33d78a6e6',
        '3f2f558a-5a9b-4475-8889-e3d163756b09'
    ]
    reports_already_in_production = reports_already_in_production + exclude_also
    for id in country_ids:
        generate_dump_files(id, 'adult', reports_already_in_production)
        generate_dump_files(id, 'site', reports_already_in_production)


# do some work
work()