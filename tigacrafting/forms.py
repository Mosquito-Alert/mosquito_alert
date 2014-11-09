import floppyforms.__future__ as forms
from models import Annotation


class Slider(forms.RangeInput):
    min = 0
    max = 100
    step = 1
    value = None
    template_name = 'slider.html'


class AnnotationForm(forms.ModelForm):
    class Meta:
        model = Annotation
        fields = ('tiger_certainty_percent', 'value_changed', 'notes')
        widgets = {
            'tiger_certainty_percent': Slider,
        }