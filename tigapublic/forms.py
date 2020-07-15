"""FORMS."""
# -*- coding: utf-8 -*-
import datetime
import json

from django import forms
from django.conf import settings
from django.http import HttpResponse


class LoginForm(forms.Form):
    """Login Form."""

    username = forms.CharField(required=True)
    password = forms.CharField(required=True)


class TinyMCEImageForm(forms.Form):
    """Standard Image form."""

    image = forms.ImageField()

    def handle_uploaded_file(self):
        """"Save the uploaded file.

        - Save it in the MEDIA_ROOT directory.
        - Add the date as a prefix to the file name.
            I.e: filename = {date}_{original_filename}
        - Return the filename.
        """
        now = datetime.datetime.now()
        filename = '%s_%s' % (
            str(now).replace(':', '_'),
            str(self.files['image'])
        )

        with open(settings.MEDIA_ROOT + '/' + filename, 'wb+') as destination:
            for chunk in self.cleaned_data['image'].chunks():
                destination.write(chunk)

        return filename

    def save(self):
        """Save the image."""
        if self.is_valid():
            filename = self.handle_uploaded_file()
            # Return the data to populate the TinyMCE form
            response = ("<script>top.$('.mce-btn.mce-open').parent().find"
                        "('.mce-textbox').val('%s').closest('.mce-form')."
                        "find('.mce-last.mce-formitem input:eq(0)')."
                        "val('%s').parent().find('input:eq(1)')."
                        "val('%s');top.$('.mce-form.mce-first > div"
                        ".mce-formitem:eq(1) input').focus();"
                        "top.$('.mce-notification').remove();</script>" %
                        (settings.MEDIA_URL + filename, '100%', ''))
            return HttpResponse(response)
        else:
            # Return an error message
            return HttpResponse("<script>alert('%s');</script>" %
                                json.dumps('\n'.join([v[0] for k, v in
                                           self.errors.items()])
                                           )
                                )
