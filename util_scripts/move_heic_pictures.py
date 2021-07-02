import os, sys
import whatimage
import logging
import pyheif
import io
from PIL import Image
from pathlib import Path
import ntpath

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import Photo

PICTURES_DIR = '/home/webuser/webapps/tigaserver/media/tigapics/'
BACKUP_DIR = '/home/webuser/webapps/original_pics/'
NUM_FILES = None
DEFAULT_NUM_FILES = 50
logging.basicConfig(filename='heic_converter.log', level=logging.DEBUG)


def get_file_list(dirpath):
    logging.debug("Getting file list")
    paths = sorted(Path(dirpath).iterdir(), key=os.path.getmtime, reverse=True)
    return paths[:NUM_FILES]


def convert_to_jpg(file):
    logging.debug("Converting file {0} to jpg".format(str(file)))
    no_ext = os.path.splitext(file)[0]
    heif_file = pyheif.read(file)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    image.save(no_ext + ".jpg", "JPEG")


def rename_photo(filename):
    logging.debug("Renaming photo in database")
    no_ext = os.path.splitext(filename)[0]
    no_route = ntpath.basename(no_ext)
    p = Photo.objects.filter(photo__icontains=no_route)
    if p.exists():
        logging.debug("Photo found, renaming to {0}".format('tigapics/' + no_route + ".jpg"))
        pic = p.first()
        pic.photo = 'tigapics/' + no_route + ".jpg"
        pic.save()


def process_file(p):
    if not os.path.isdir(p):
        with open(p, 'rb') as f:
            data = f.read()
        fmt = whatimage.identify_image(data)
        if fmt == 'heic':
            logging.debug("Found heic file! {0} files".format(str(p)))
            print("{0} - {1}".format(p, fmt))
            convert_to_jpg(p)
            rename_photo(p)
            move_file_to_backup(p, BACKUP_DIR)


def process_files(file_list):
    for p in file_list:
        process_file(p)


def move_file_to_backup(f,backup_dir):
    logging.debug("Moving file {0} to backup directory {1}".format(str(f),backup_dir))
    no_route = ntpath.basename(f)
    os.rename(str(f), backup_dir + no_route)


if __name__ == "__main__":
    try:
        NUM_FILES = int(sys.argv[1])
        logging.debug("Starting scan of {0} files".format(str(NUM_FILES)))
    except:
        NUM_FILES = DEFAULT_NUM_FILES
        logging.debug("Starting scan of {0} files".format(str(NUM_FILES)))
    paths = get_file_list(PICTURES_DIR)
    process_files(paths)
