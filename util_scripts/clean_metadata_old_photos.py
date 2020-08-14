import os, sys
#proj_path = "/home/webuser/webapps/tigaserver/"
proj_path = "/home/christian/Documentos/MosquitoAlert/tigatrapp-server-python36/tigatrapp-server"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from os import listdir
from os.path import isfile, join
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from tigaserver_app.models import Photo
from io import BytesIO
from django.core.files import File
from tqdm import tqdm

tigapics_path = "../media/tigapics/"


def cleanPhoto():
    numFotos = len(listdir(tigapics_path))
    #for t in listdir(tigapics_path):
    print()
    print("Removing metadata from images, this will take some time.")
    print()
    for t in tqdm(listdir(tigapics_path), desc="Test"):
        #print("*************")
        #print(t)
        imageExif = Image.open(tigapics_path + t)._getexif()

        nomPhoto = "tigapics/" + str(t)

        exif_data = {}
        if imageExif:
            for tag, value in imageExif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for x in value:
                        sub_decoded = GPSTAGS.get(x, x)
                        gps_data[sub_decoded] = value[x]
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
        exif_data = exif_data

        if "GPSInfo" in exif_data:
            gps_info = exif_data["GPSInfo"]
            gps_latitude = get_if_exist(gps_info, "GPSLatitude")
            gps_latitude_ref = get_if_exist(gps_info, 'GPSLatitudeRef')
            gps_longitude = get_if_exist(gps_info, 'GPSLongitude')
            gps_longitude_ref = get_if_exist(gps_info, 'GPSLongitudeRef')
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = convert_to_degress(gps_latitude)
                if gps_latitude_ref != "N":
                    lat = 0 - lat
                lng = convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lng = 0 - lng

                utmX = lat
                utmY = lng
                #print("UTMX: ", utmX)
                #print("UTMY: ", utmY)

                #print(nomPhoto)
                q = Photo.objects.filter(photo__icontains=nomPhoto).update(utmX=utmX, utmY=utmY)

        #f = Photo.objects.filter(photo__icontains=nomPhoto)

        image_file_path = tigapics_path + str(t)
        image = Image.open(image_file_path)
        data = list(image.getdata())
        scrubbed_image = Image.new(image.mode, image.size)
        scrubbed_image.putdata(data)
        #scrubbed_image_io = BytesIO()
        scrubbed_image.save(tigapics_path + str(t))
        #photo = File(scrubbed_image_io, name=str(t))
        #print("------------")
        pass
    print()
    print("Progress finished.")
    print()
    return True






def get_if_exist(data, key):
    if key in data:
        return data[key]
    return None

def convert_to_degress(value):
    degrees = value[0]
    minutes = value[1] / 60.0
    seconds = value[2] / 3600.0

    return round(degrees + minutes + seconds, 5)


cleanPhoto()