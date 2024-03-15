from django.test import TestCase
from django.contrib.auth.models import User
import tigaserver_project.settings as conf
from tigacrafting.models import Alert
from tigaserver_app.views import check_status_in_shapefile, write_status_to_shapefile, get_new_status
import shutil, os

# ./manage.py test tigacrafting.test_shapefiles

class ShapefileTests(TestCase):

    fixtures = ['reritja_like.json', 'alert.json', 'categories.json']
    path_to_shapefile = conf.BASE_DIR +'/tigacrafting/fixtures/shapefile/'
    categories = {
        '4': 'albopictus',
        '5': 'aegypti',
        '6': 'japonicus',
        '7': 'koreicus',
        '10': 'culex',
    }

    def setUp(self):
        shutil.copyfile(self.path_to_shapefile + 'status_2303.shp', self.path_to_shapefile + 'status_2303_test.shp')
        shutil.copyfile(self.path_to_shapefile + 'status_2303.dbf', self.path_to_shapefile + 'status_2303_test.dbf')
        shutil.copyfile(self.path_to_shapefile + 'status_2303.prj', self.path_to_shapefile + 'status_2303_test.prj')
        shutil.copyfile(self.path_to_shapefile + 'status_2303.shx', self.path_to_shapefile + 'status_2303_test.shx')
        shutil.copyfile(self.path_to_shapefile + 'status_2303.cpg', self.path_to_shapefile + 'status_2303_test.cpg')
        self.reritja_user = User.objects.get(pk=25)
        conf.PRESENCE_SHAPEFILE = self.path_to_shapefile + 'status_2303_test.shp'

    def tearDown(self):
        os.remove(self.path_to_shapefile + 'status_2303_test.shp')
        os.remove(self.path_to_shapefile + 'status_2303_test.dbf')
        os.remove(self.path_to_shapefile + 'status_2303_test.prj')
        os.remove(self.path_to_shapefile + 'status_2303_test.shx')
        os.remove(self.path_to_shapefile + 'status_2303_test.cpg')


    def test_shapefile_read(self):
        alert = Alert.objects.get(pk=20230034)
        status_info = check_status_in_shapefile('4',alert.loc_code,alert.species, conf.PRESENCE_SHAPEFILE)
        self.assertEqual( status_info['status'], 'absent',  "Status for albopictus should be absent, is {0}".format(status_info['status']))

    def test_shapefile_write(self):
        alert = Alert.objects.get(pk=20230034)
        status_info_write = write_status_to_shapefile(alert.loc_code, 'albopictus', 'reported', conf.PRESENCE_SHAPEFILE)
        self.assertEqual( status_info_write['new_status'], 'reported', "New status in shapefile should be reported, is {0}".format(status_info_write['new_status']) )
        # make sure and reread info
        status_info_read = check_status_in_shapefile('4', alert.loc_code, alert.species, conf.PRESENCE_SHAPEFILE)
        self.assertEqual(status_info_read['status'], 'reported', "Status for albopictus should be reported, is {0}".format(status_info_read['status']))

    def test_get_new_status(self):
        expert_validation_category = '4'
        status_in_location = 'absent'
        loc_code = 'AT221'
        new_status_data = get_new_status(expert_validation_category,status_in_location,loc_code)
        self.assertTrue( new_status_data['new_status'] == 'reported', "New status should be reported, is {0}".format( new_status_data['new_status'] ) )
