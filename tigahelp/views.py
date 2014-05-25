from django.shortcuts import render

# Create your views here.


def show_help_ca(request):
    context = {}
    return render(request, 'tigahelp/ca.html', context)


def show_help_es(request):
    context = {}
    return render(request, 'tigahelp/es.html', context)


def show_help_en(request):
    context = {}
    return render(request, 'tigahelp/en.html', context)
