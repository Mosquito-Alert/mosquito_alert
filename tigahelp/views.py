from django.shortcuts import render
from django.template.loader import TemplateDoesNotExist

# Create your views here.
def show_app_license(request):
    language = request.LANGUAGE_CODE
    context = {}
    if language == 'ca':
        return render(request, 'tigahelp/app_license_ca.html', context)
    if language == 'es':
        return render(request, 'tigahelp/app_license_es.html', context)
    if language == 'en':
        return render(request, 'tigahelp/app_license_en.html', context)
    if language == 'zh-cn':
        return render(request, 'tigahelp/app_license_en.html', context)