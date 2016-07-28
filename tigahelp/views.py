from django.shortcuts import render

# Create your views here.


def show_about(request, platform, language):
    context = {}
    # We ignore platform for now
    # if platform == 'ios':
    #     if language == 'ca':
    #         return render(request, 'tigahelp/about_ios_ca.html', context)
    #     if language == 'es':
    #         return render(request, 'tigahelp/about_ios_es.html', context)
    #     if language == 'en':
    #         return render(request, 'tigahelp/about_ios_en.html', context)
    # else:
    if language == 'ca':
        return render(request, 'tigahelp/about_ca.html', context)
    if language == 'es':
        return render(request, 'tigahelp/about_es.html', context)
    if language == 'en':
        return render(request, 'tigahelp/about_en.html', context)


def show_credit_image(request):
    context = {}
    return render(request, 'tigahelp/credit_image.html', context)


def show_help(request, platform, language):
    context = {}
    if language == 'ca':
        return render(request, 'tigahelp/help_ca.html', context)
    if language == 'es':
        return render(request, 'tigahelp/help_es.html', context)
    if language == 'en':
        return render(request, 'tigahelp/help_en.html', context)


def show_license(request, platform, language):
    context = {}
    if language == 'ca':
        return render(request, 'tigahelp/license_ca.html', context)
    if language == 'es':
        return render(request, 'tigahelp/license_es.html', context)
    if language == 'en':
        return render(request, 'tigahelp/license_en.html', context)


def show_policies(request):
    context = {}
    return render(request, 'tigahelp/policies.html', context)


def show_privacy(request):
    language = request.LANGUAGE_CODE
    context = {}
    if language == 'ca':
        return render(request, 'tigahelp/privacy_ca.html', context)
    if language == 'es':
        return render(request, 'tigahelp/privacy_es.html', context)
    if language == 'en':
        return render(request, 'tigahelp/privacy_en.html', context)


def show_terms(request):
    language = request.LANGUAGE_CODE
    context = {}
    if language == 'ca':
        return render(request, 'tigahelp/terms_ca.html', context)
    if language == 'es':
        return render(request, 'tigahelp/terms_es.html', context)
    if language == 'en':
        return render(request, 'tigahelp/terms_en.html', context)
