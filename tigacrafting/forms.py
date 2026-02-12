import floppyforms.__future__ as forms
from tigaserver_app.models import Report


class PhotoGrid(forms.ModelForm):
    fastUpload = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'fastUploadClass'}), required=False, initial=False)
    other_species = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'otherSpeciesClass'}), required=False, initial=False)
    probably_culex = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'probablyCulexClass'}), required=False,initial=False)
    probably_albopictus = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'probablyAlbopictusClass'}), required=False, initial=False)
    sure_albopictus = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'sureAlbopictusClass'}), required=False, initial=False)
    not_sure = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'notSureClass'}), required=False, initial=False)
    hide = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'hideClass'}), required=False, initial=False)

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