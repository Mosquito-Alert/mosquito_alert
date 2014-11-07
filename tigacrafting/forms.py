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
        fields = ('tiger_certainty_percent', 'tiger_certainty_cats', 'tiger_certainty_bool')
        widgets = {
            'tiger_certainty_percent': Slider,
            'tiger_certainty_cats': forms.Select,
            'tiger_certainty_bool': forms.CheckboxInput,
        }

    def clean_num(self):
        num = self.cleaned_data['num']
        if not 0 <= num <= 100:
            raise forms.ValidationError("Enter a value between 0 and 100")

        if not num % 1 == 0:
            raise forms.ValidationError("Enter an integer")
        return num