# coding=utf-8
"""Constants accross the application."""
from django.conf import settings

maxReports = 300
maxDownloads = 300
managers_group = 'gestors'
superusers_group = 'supermosquito'
epidemiologist_editor_group = 'epidemiologist'
epidemiologist_viewer_group = 'epidemiologist_viewer'
epidemiologist_group = 'epidemiologist'

"""
All roles allowed

  - sorted by permissivity (most permissive appears first)
"""
user_roles = [superusers_group, managers_group]


####################
# EXPORT EXCEL/CSV #
####################

"""
All fields available.

Each field is a tuple. For each tuple:
  - The first element is the name of the DB column (string)
  - The second element is the name of the Excel/CSV column (string)

Except for the fields restricted to specific roles, in such case:
  - The first element remains the same.
  - The second element is a dict with these attributes:
      - label (string): the name of the Excel/CSV column
      - permissions (list): the roles allowed to see this field
"""
fields_available = [
    ('version_uuid', 'ID'),
    ('user_id', {
        'label': '(PRIVATE COLUMN!!) User',
        'permissions':  [superusers_group, managers_group]
    }),
    ('observation_date', 'Date'),
    ('lon', 'Longitude'),
    ('lat', 'Latitude'),
    ('ref_system', 'Ref. System'),
    ('municipality__nombre', 'Municipality'),
    ('type', 'Type'),
    # ('t_q_1', {
    #     'label': 'Adult question 1',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('t_a_1', {
    #     'label': 'Adult answer 1',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('t_q_2', {
    #     'label': 'Adult question 2',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('t_a_2', {
    #     'label': 'Adult answer 2',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('t_q_3', {
    #     'label': 'Adult question 3',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('t_a_3', {
    #     'label': 'Adult answer 3',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_q_1', {
    #     'label': 'Site question 1',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_a_1', {
    #     'label': 'Site answer 1',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_q_2', {
    #     'label': 'Site question 2',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_a_2', {
    #     'label': 'Site answer 2',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_q_3', {
    #     'label': 'Site question 3',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_a_3', {
    #     'label': 'Site answer 3',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_q_4', {
    #     'label': 'Site question 4',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    # ('s_a_4', {
    #     'label': 'Site answer 4',
    #     'permissions':  [superusers_group, managers_group]
    # }),
    ('expert_validated', 'Expert validated'),
    ('private_webmap_layer', 'Expert validation result'),
    ('single_report_map_url', 'Map link'),
    ('note', {
         'label': '(PRIVATE COLUMN!!) Tags',
         'permissions': [superusers_group]
    })
]


################
# STORM DRAINS #
################

"""Required fields. Key should be the same as StormModel fields."""
compulsatory_stormdrain_fields = {
    'code': ['code', 'codigo', 'codi'],
    'lat': ['latitud', 'lat', 'y_etrs89'],
    'lon': ['longitud', 'lon', 'x_etrs89'],
    'date': ['date', 'fecha', 'data'],
    'water': ['h2o', 'water', 'agua', 'aigua'],
    'type': ['e_tipo', 'forma', 'shape', 'type']
}

"""Optional fields. Key should be the same as StormModel fields."""
optional_stormdrain_fields = {
    'idalfa': ['idalfa'],
    'size': ['mida', 'size', 'tamaño'],
    'model': ['modelo', 'tipus', 'model'],
    'activity': ['activity', 'activitat', 'actividad'],
    'species1': ['specie 1', 'esp1', 'especie 1'],
    'species2': ['specie 2', 'esp2', 'especie 2'],
    'treatment': ['treatment', 'tratamiento', 'trat'],
    'messure': ['messure'],
    'sand': ['sand', 'arena', 'sorra'],
    'municipality': ['municipality', 'municipio', 'municipi'],
    'icon': ['icon']
}

"""Thematic fields."""
tematic_fields = ['water', 'sand', 'treatment',
                  'species1', 'species2', 'activity', 'type', 'date']

"""Default style. Style to use when creating a new version."""
defaultStormDrainStyle = {'version_data': False, "categories": [{
    "color": '#ff0000',
    "conditions": [{
        "field": 'water',
        "value": 'true',
        "operator": '='
    }]
}]}

true_values = ['si', 'sí', 'yes', 'true', '1']
false_values = ['no', 'false', '0', '-1']
null_values = ['null', 'nulo', 'nul', '-']
stormdrain_templates_path = (settings.BASE_DIR +
                             '/tigapublic/templates/imbornales')

################
# EPIDEMIOLOGY #
################

"""Required fields. Key should be the same as epidemiology fields."""

compulsatory_epidemiology_fields = {
    'id': ['code', 'codigo', 'codi', 'id', 'numero'],
    'lat': ['latitud', 'lat', 'latitude'],
    'lon': ['longitud', 'lon', 'longitude'],
    'date_symptom': ['date_symptoms', 'inicio_sintomas', 'inici_simptomes'],
    'country': ['visited_country', 'pais_visitado', 'pais_visitat'],
    'patient_state': ['patient_state', 'estado', 'estat'],
    'health_center': ['center', 'centro', 'centre', 'centre_dia'],
    'year': ['año', 'any', 'year'],
    'province': ['province', 'provincia', 'prov'],
    'age': ['age', 'edad', 'edat', 'edatany'],
}

optional_epidemiology_fields = {
    'date_arribal': ['date_arribal', 'fecha_llegada', 'data_arribada'],
    'date_notification': ['date_notification', 'fecha_notificacion',
                          'data_notificacio'],
    'comments': ['comments', 'comentarios', 'comentaris', 'observacio']
}

epi_templates_path = settings.BASE_DIR + '/tigapublic/templates/epi'
epi_form_file = 'epidemiology-file'


#############
# USERFIXES #
#############
"""Size of the grid (in degrees).

This value indicates the minimum distance between the points stored in the
table tigaserver_app_fix. Do not change this value unless it has already
changed in that table."""
gridsize = 0.05

#############
# MODELS    #
#############
"""Params for mosquito/vector models layer"""

# BITING RATES (FILES LOCATION)
biting_rates_models_folder = (settings.BASE_DIR +
                              '/static/tigapublic/models/biting/')
biting_file_name = 'mascp_monthly'
biting_file_ext = '.csv'

# GRID VECTOR MODELS PROPERTIES
grid_vectors_models_folder = (settings.BASE_DIR +
                              '/static/tigapublic/models/vector/grid/')

vector_file_name = 'mascp_monthly'
vector_file_ext = '.csv'
vector_days_ahead = 7

# MUNICIPALITIES VECTOR MODELS PROPERTIES
municipalities_vector_models_folder = (
    settings.BASE_DIR +
    '/static/tigapublic/models/vector/municipalities/'
    )
municipalities_vector_file_name = 'mascp_monthly'
municipalities_vector_file_ext = '.csv'

# AVAILABLE MOSQUITO SPECIES
vectors = ['tig', 'jap', 'yfv']

# AVAILABLE ILLNESS MODELS
virus = ['den', 'chk', 'yf', 'wnv', 'zk']

# MUNICIPALITIES VIRUS MODELS PROPERTIES
municipalities_virus_models_folder = (
    settings.BASE_DIR +
    '/static/tigapublic/models/virus/municipalities/'
    )
municipalities_virus_file_name = 'mascp_monthly'
municipalities_virus_file_ext = '.csv'

# MUNICIPALITIES GEOMETRIES BY CC.AA
municipalities_geom_folder = (
    settings.BASE_DIR +
    '/static/tigapublic/geoms/ccaa/'
    )
municipalities_geom_file_name = 'ccaa_'
municipalities_geom_file_ext = '.geojson'

# UNCERTAINTY GEOMETRIES BY CC.AA
municipalities_sd_geom_folder = (
    settings.BASE_DIR +
    '/static/tigapublic/geoms/ccaa/'
    )
municipalities_sd_geom_file_name = 'ccaa_sd_'
municipalities_sd_geom_file_ext = '.geojson'

tiles_path = (settings.BASE_DIR +
              '/static/tigapublic/tiles')
