from django.forms import ModelForm
from tigaserver_app.models import Photo


class PhotoForm(ModelForm):
    class Meta:
        model = Photo

