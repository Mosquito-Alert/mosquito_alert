from django.http import HttpResponseRedirect
from django.shortcuts import render
from webapp.forms import ReportForm


def report(request):
    if request.method == 'POST':  # If the form has been submitted...
        form = ReportForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            form.save()
            return HttpResponseRedirect('/api/')  # Redirect after POST
    else:
        form = ReportForm() # An unbound form

    return render(request, 'webapp/report.html', {
        'form': form,
    })
