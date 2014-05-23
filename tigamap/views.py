from django.shortcuts import render
from django.http import HttpResponse
from tigaserver_app.models import Fix


def index(request):
    return HttpResponse("Hello, world. You're at the poll index.")


def show_webmap_app(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/app.html', context)


def show_embedded_webmap(request):
    fix_list = Fix.objects.all()
    context = {'fix_list': fix_list}
    return render(request, 'tigamap/embedded.html', context)