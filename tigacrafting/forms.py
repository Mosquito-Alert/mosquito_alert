import floppyforms.__future__ as forms
from tigacrafting.models import Annotation, MoveLabAnnotation, ExpertReportAnnotation
from tigaserver_app.models import Report


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


class MovelabAnnotationForm(forms.ModelForm):
    class Meta:
        model = MoveLabAnnotation
        fields = ('tiger_certainty_category', 'certainty_notes', 'hide', 'edited_user_notes')


class ExpertReportAnnotationForm(forms.ModelForm):

    class Meta:
        model = ExpertReportAnnotation
        fields = ('tiger_certainty_category', 'aegypti_certainty_category', 'tiger_certainty_notes', 'site_certainty_category', 'site_certainty_notes', 'edited_user_notes', 'message_for_user', 'best_photo', 'status', 'linked_id', 'validation_complete', 'tags', 'simplified_annotation', 'category', 'complex', 'validation_value', 'other_species')
        widgets = {
            'tiger_certainty_category': forms.HiddenInput,
            'aegypti_certainty_category': forms.HiddenInput,
            'best_photo': forms.HiddenInput,
            'tiger_certainty_notes': forms.Textarea(attrs={'rows': 4}),
            'site_certainty_notes': forms.Textarea(attrs={'rows': 4}),
            #'edited_user_notes': forms.Textarea(attrs={'rows': 4}),
            # Public Note
            'edited_user_notes': forms.HiddenInput,
            #'message_for_user': forms.Textarea(attrs={'rows': 4}),
            'message_for_user': forms.HiddenInput,
            'tags': forms.HiddenInput,
            'simplified_annotation': forms.HiddenInput,
            'category': forms.HiddenInput,
            'complex': forms.HiddenInput,
            'validation_value': forms.HiddenInput,
            'other_species': forms.HiddenInput
        }


class SuperExpertReportAnnotationForm(forms.ModelForm):

    class Meta:
        model = ExpertReportAnnotation
        fields = ('tiger_certainty_category', 'aegypti_certainty_category', 'tiger_certainty_notes', 'site_certainty_category', 'site_certainty_notes', 'status', 'linked_id', 'edited_user_notes', 'message_for_user', 'best_photo', 'revise', 'validation_complete','tags', 'category', 'complex', 'validation_value', 'other_species')
        widgets = {
            'tiger_certainty_category': forms.HiddenInput,
            'aegypti_certainty_category': forms.HiddenInput,
            'best_photo': forms.HiddenInput,
            'revise': forms.HiddenInput,
            'tiger_certainty_notes': forms.Textarea(attrs={'rows': 4}),
            'site_certainty_notes': forms.Textarea(attrs={'rows': 4}),
            #'edited_user_notes': forms.Textarea(attrs={'rows': 4}),
            # Public Note
            'edited_user_notes': forms.HiddenInput,
            #'message_for_user': forms.Textarea(attrs={'rows': 4}),
            'message_for_user': forms.HiddenInput,
            'tags': forms.HiddenInput,
            'category': forms.HiddenInput,
            'complex': forms.HiddenInput,
            'validation_value': forms.HiddenInput,
            'other_species': forms.HiddenInput
        }

class PhotoGrid(forms.ModelForm):
    fastUpload = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'fastUploadClass'}), required=False, initial=False)

    #rodalref = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'boolRodRef'}), required=False)
    class Meta:
        model = Report
        fields = ('hide',)

class LicenseAgreementForm(forms.Form):
    agreed = forms.BooleanField(label="Yes, I have read and agree to the user agreement terms above")

    def clean_agreed(self):
        agreed = self.cleaned_data['agreed']
        if not agreed:
            raise forms.ValidationError("Sorry, you must agree to the terms before proceeding to the EntoLab")
        return agreed