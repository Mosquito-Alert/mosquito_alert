# coding=utf-8
from django.conf import settings

maxReports = 300
maxDownloads = 300
managers_group ='gestors'
superusers_group = 'supermosquito'

#key should be the same as StormModel fields
compulsatory_stormdrain_fields = {
    'code':['code', 'codigo', 'codi'],
    'lat': ['latitud','lat','y_etrs89'],
    'lon': ['longitud','lon','x_etrs_89'],
    'date':['date','fecha','data'],
    'water':['h2o','water','agua','aigua'],
    'type':['e_tipo','forma','shape','type']
}

optional_stormdrain_fields = {
    'idalfa':['idalfa'],
    'size':['mida','size'],
    'model':['modelo','tipus', 'model'],
    'activity':['activity', 'activitat', 'actividad'],
    'specie1':['specie 1','esp1','especie 1'],
    'specie2':['specie 2','esp2','especie 2'],
    'treatment':['treatment','tratamiento','trat'],
    'messure':['messure'],
    'sand':['sand','arena','sorra'],
    'municipality':['municipality','municipio','municipi'],
    'icon':['icon']
}

tematic_fields=['water','sand','treatment','species1','species2','activity','type','date']

true_values = ['si', 'sí', 'yes', 'true', '1']
false_values= ['no', 'false', '0','-1']

stormdrain_templates_path = settings.BASE_DIR + '/tigapublic/templates'
