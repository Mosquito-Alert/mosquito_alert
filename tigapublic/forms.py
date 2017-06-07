from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True)

class NotificationImageForm(forms.Form):
    image = forms.ImageField()
