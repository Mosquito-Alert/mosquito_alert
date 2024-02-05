from tigaserver_app.models import NutsEurope
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


class NutsOneDict(metaclass=SingletonMeta):

    nuts_one_name_mapping = {}

    def populate_nuts_one_name_mapping(self):
        nuts_one_qs = NutsEurope.objects.filter(levl_code=1).values('nuts_id','name_latn')
        nuts_array = [(d['nuts_id'], d['name_latn']) for d in nuts_one_qs]
        self.nuts_one_name_mapping = dict(nuts_array)

    def get_nuts_one(self, nuts_code):
        if nuts_code is not None:
            nuts_one_code = nuts_code[:3]
            return self.nuts_one_name_mapping.get(nuts_one_code, 'Unknown')
        return 'Unknown'

    def __init__(self):
        self.populate_nuts_one_name_mapping()