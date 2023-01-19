import os, sys
import logging
import pyheif
from PIL import Image
from pathlib import Path
import ntpath
import magic
import rawpy
from django.core.mail import send_mail

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from tigaserver_app.models import Photo
from logging.handlers import RotatingFileHandler
from datetime import datetime

PICTURES_DIR = '/home/webuser/webapps/tigaserver/media/tigapics/'
BACKUP_DIR = '/home/webuser/webapps/original_pics/'
NUM_FILES = None
DEFAULT_NUM_FILES = 100

logger = logging.getLogger('heic_converter')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("heic_converter.log", maxBytes=1000000, backupCount=5)
logger.addHandler(handler)


def get_file_list(dirpath):
    logger.debug("Getting file list")
    paths = sorted(Path(dirpath).iterdir(), key=os.path.getmtime, reverse=True)
    return paths[:NUM_FILES]


def heic_to_jpg(file):
    try:
        logger.debug("Converting file {0} to jpg".format(str(file)))
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
    except Exception as e:
        print("{0} {1}".format(str(file),e))


def dng_to_jpg(file):
    try:
        logger.debug("Converting file {0} to jpg".format(str(file)))
        no_ext = os.path.splitext(file)[0]
        with rawpy.imread(str(file)) as raw:
            image = Image.frombytes('RGB', (raw.sizes.raw_width, raw.sizes.raw_height), raw.postprocess())
            image.save(no_ext + ".jpg", format='jpeg')
    except Exception as e:
        print("{0} {1}".format(str(file),e))


def webp_to_jpg(file):
    try:
        logger.debug("Converting file {0} to jpg".format(str(file)))
        no_ext = os.path.splitext(file)[0]
        image = Image.open(file).convert('RGB')
        image.save(no_ext + ".jpg", format='jpeg')
    except Exception as e:
        print("{0} {1}".format(str(file),e))


def rename_photo(filename):
    logger.debug("Renaming photo in database")
    no_ext = os.path.splitext(filename)[0]
    no_route = ntpath.basename(no_ext)
    p = Photo.objects.filter(photo__icontains=no_route)
    if p.exists():
        logger.debug("Photo found, renaming to {0}".format('tigapics/' + no_route + ".jpg"))
        pic = p.first()
        pic.photo = 'tigapics/' + no_route + ".jpg"
        pic.save()


def process_file(p):
    if not os.path.isdir(p):
        filename, file_extension = os.path.splitext(p)
        if file_extension == '.dng':
            logger.debug("Found dng/raw file! {0} files".format(str(p)))
            dng_to_jpg(p)
            rename_photo(p)
            move_file_to_backup(p, BACKUP_DIR)
        elif file_extension == '.DNG':
            logger.debug("Found jpeg with heic/dng extension! {0} files".format(str(p)))
            rename_photo(p)
            # jpeg file with extension heic, but it's harmless
            os.rename(p, filename + '.jpg')
        elif file_extension == '.heic':
            logger.debug("Found heic file! {0} files".format(str(p)))
            heic_to_jpg(p)
            rename_photo(p)
            move_file_to_backup(p, BACKUP_DIR)
        elif file_extension == '.HEIC':
            logger.debug("Found jpeg with heic/dng extension! {0} files".format(str(p)))
            rename_photo(p)
            # jpeg file with extension heic, but it's harmless
            os.rename(p, filename + '.jpg')
        elif file_extension == '.webp':
            logger.debug("Found webp file! {0} files".format(str(p)))
            webp_to_jpg(p)
            rename_photo(p)
            move_file_to_backup(p, BACKUP_DIR)
        elif file_extension in [".JPEG", ".JPG", ".jpg", ".jpeg", ".png", ".PNG", ".GIF", ".gif"]:
            pass
        else:
            logger.debug("Found file with weird extension {0} file, {1} extension".format(str(p), file_extension))
            fmt = magic.from_file(str(p))
            if fmt.startswith('JPEG image data'):
                rename_photo(p)
                os.rename(p, filename + '.jpg')
            else:
                #Don't know what this is
                body = "Found weird file in media/tigapics, file {0} - extension {1}".format( str(p), file_extension)
                send_mail('[MA] - Weird file in media/tigapics', body, 'a.escobar@creaf.uab.cat', ['a.escobar@creaf.uab.cat'], fail_silently=False, )


def process_files(file_list):
    for p in file_list:
        process_file(p)


def move_file_to_backup(f,backup_dir):
    logger.debug("Moving file {0} to backup directory {1}".format(str(f),backup_dir))
    no_route = ntpath.basename(f)
    os.rename(str(f), backup_dir + no_route)


def get_now_timestamp():
    now = datetime.now()
    return now.strftime("%m/%d/%Y, %H:%M:%S")


if __name__ == "__main__":
    logger.debug("**** Starting run at {0} ****".format(get_now_timestamp()))
    try:
        NUM_FILES = int(sys.argv[1])
        logger.debug("Starting scan of {0} files".format(str(NUM_FILES)))
    except:
        NUM_FILES = DEFAULT_NUM_FILES
        logger.debug("Starting scan of {0} files".format(str(NUM_FILES)))
    paths = get_file_list(PICTURES_DIR)
    process_files(paths)
    logger.debug("**** Finished run at {0} *****".format(get_now_timestamp()))
