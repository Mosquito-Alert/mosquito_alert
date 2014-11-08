import floppyforms.__future__ as forms
from models import Annotation


class Slider(forms.RangeInput):
    min = 0
    max = 100
    step = 1
    template_name = 'slider.html'


class AnnotationForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = ('tiger_certainty_percent', 'notes')
        widgets = {
            'tiger_certainty_percent': Slider,
        }