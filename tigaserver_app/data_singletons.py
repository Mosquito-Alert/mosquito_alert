from tigaserver_app.models import NutsEurope, MunicipalitiesNatCode
class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


# Your singleton class
class CountryDict(metaclass=SingletonMeta):

    country_name_mapping = {}

    def populate_country_name_mapping(self):
        country_qs = NutsEurope.objects.filter(levl_code=0).values('cntr_code','name_latn')
        country_array = [(d['cntr_code'], d['name_latn']) for d in country_qs]
        self.country_name_mapping = dict(country_array)

    def get_country(self, loc_code):
        if loc_code is not None:
            cntr_code = loc_code[:2]
            return self.country_name_mapping.get(cntr_code, 'Unknown')
        return 'Unknown'

    def __init__(self):
        self.populate_country_name_mapping()

class NutsDict(metaclass=SingletonMeta):
    nuts_zero_name_mapping = {}
    nuts_one_name_mapping = {}
    nuts_two_name_mapping = {}
    nuts_three_name_mapping = {}

    nuts_name_mapping = [
        nuts_zero_name_mapping,
        nuts_one_name_mapping,
        nuts_two_name_mapping,
        nuts_three_name_mapping
    ]

    def populate_nuts_table(self,nuts_level):
        nuts_qs = NutsEurope.objects.filter(levl_code=nuts_level).values('nuts_id', 'name_latn')
        nuts_array = [(d['nuts_id'], d['name_latn']) for d in nuts_qs]
        self.nuts_name_mapping[nuts_level] = dict(nuts_array)

    def get_nuts_name(self, nuts_code, nuts_level):
        idx = nuts_level + 2
        if nuts_code is not None:
            nuts_lvl_code = nuts_code[:idx]
            return self.nuts_name_mapping[nuts_level].get(nuts_lvl_code, 'Unknown')
        return 'Unknown'

    def __init__(self):
        self.populate_nuts_table(0)
        self.populate_nuts_table(1)
        self.populate_nuts_table(2)
        self.populate_nuts_table(3)

class MunicipalitiesDict(metaclass=SingletonMeta):
    municipalities_mapping = {}

    def populate_municipalities_table(self):
        municipalities_qs = MunicipalitiesNatCode.objects.all().values('natcode', 'nameunit')
        municipalities_array = [(d['natcode'], d['nameunit']) for d in municipalities_qs]
        self.municipalities_mapping = dict(municipalities_array)

    def get_municipality_name(self, natcode):
        return self.municipalities_mapping.get(natcode,'Unknown')

    def __init__(self):
        self.populate_municipalities_table()