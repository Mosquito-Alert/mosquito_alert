from django.http import HttpResponse, HttpResponseRedirect
from tigaserver_app.models import Photo
from django.views.decorators.csrf import csrf_exempt
from tigaserver_app.forms import PhotoForm
from django.shortcuts import render

""""
@csrf_exempt
def upload_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            return HttpResponseRedirect('http://localhost:8000/admin')
    else:
        form = PhotoForm()

    return render(request, 'tigaserver_app/photo_form.html', {'form': form})

"""

@csrf_exempt
def upload_photo(request):
    if request.method == 'POST':

        for thisFile in request.FILES.items():
            new_file = Photo(photo=thisFile)
            new_file.save()


        response_data = {"result:OK"}
        return HttpResponse(response_data, mimetype='application/json')

    else:
        response_data = {"success": "No a post request"}
        return HttpResponse(response_data, mimetype='application/json')
