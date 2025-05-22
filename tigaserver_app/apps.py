from django.apps import AppConfig

from timezonefinder import TimezoneFinder

from PIL import Image, TiffImagePlugin
from .pillow_utils import register_raw_opener
from pillow_heif import register_heif_opener

# NOTE: calling Image.init() before register is crucial to import first
# native plugins from pillow before the custom one.
# Besides, there is not accept() function defined for raw_opener, which
# does not check for any magic number (bytes prefix) for accept only certain
# types of images.
Image.init()
register_heif_opener()
register_raw_opener()

if TiffImagePlugin.TiffImageFile.format in Image.ID:
    #NOTE: Tiff is accepting magic numbers from RAW photos. Should be the last in the chain.
    Image.ID.remove(TiffImagePlugin.TiffImageFile.format)
    Image.ID.append(TiffImagePlugin.TiffImageFile.format)

class TigaserverApp(AppConfig):
    name = "tigaserver_app"
    label = "tigaserver_app"
    verbose_name = "Tigaserver_App"

    def ready(self):
        # Initialize the TimezoneFinder object and store it as a class attribute
        # due to the first load is quite slow.
        self.timezone_finder = TimezoneFinder()