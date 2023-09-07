from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import TaxonClassificationCandidate


class TaxonClassificationCandidateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["is_seed"].initial = True
        self.fields["is_seed"].disabled = True

        if self.instance.pk and not self.instance.is_seed:
            for f in self.fields:
                self.fields[f].disabled = True

    class Meta:
        model = TaxonClassificationCandidate
        fields = ["label", "probability", "is_seed"]
        widgets = {
            "probability": forms.NumberInput(
                attrs={
                    "max": "1",  # For maximum number
                    "min": "0",  # For minimum number
                }
            ),
        }


class TaxonClassificationCategorizedProbabilityCandidateForm(TaxonClassificationCandidateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk or self.instance.is_seed:
            self.fields["probability"] = forms.TypedChoiceField(
                choices=(("1.0", _("I'm sure")), ("0.75", _("I'm doubting"))), coerce=Decimal, required=True
            )

    class Meta(TaxonClassificationCandidateForm.Meta):
        pass
