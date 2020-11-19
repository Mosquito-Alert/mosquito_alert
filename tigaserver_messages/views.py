from django.shortcuts import render

# Create your views here.
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.template import RequestContext
from django_messages.utils import format_quote, get_user_model, get_username_field
from django.shortcuts import render_to_response, get_object_or_404
from tigaserver_messages.forms import ComposeForm
from django_messages.models import Message
from django.utils.translation import ugettext as _
from django.shortcuts import render
import json

User = get_user_model()

def tokenize_recipients(recipients):
    results = []
    for recipient in recipients:
        results.append({ "text": recipient.first_name + " " + recipient.last_name, "value" : recipient.username })
    return json.dumps(results)

@login_required
def compose(request, recipient=None, form_class=ComposeForm,
        template_name='django_messages/compose.html', success_url=None, recipient_filter=None):
    """
    Displays and handles the ``form_class`` form to compose new messages.
    Required Arguments: None
    Optional Arguments:
        ``recipient``: username of a `django.contrib.auth` User, who should
                       receive the message, optionally multiple usernames
                       could be separated by a '+'
        ``form_class``: the form-class to use
        ``template_name``: the template to use
        ``success_url``: where to redirect after successfull submission
    """
    if request.method == "POST":
        sender = request.user
        form = form_class(request.POST, recipient_filter=recipient_filter)
        if form.is_valid():
            form.save(sender=request.user)
            messages.info(request, _(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_inbox')
            if 'next' in request.GET:
                success_url = request.GET['next']
            return HttpResponseRedirect(success_url)
    else:
        form = form_class()
        if recipient is not None:
            recipients = [u for u in User.objects.filter(**{'%s__in' % get_username_field(): [r.strip() for r in recipient.split('+')]})]
            form.fields['recipient'].initial = recipients
    return render(request, template_name, {
        'form': form,
    })

@login_required
def compose_w_data(request, recipient=None, body=None, subject=None, form_class=ComposeForm,template_name='django_messages/compose.html', success_url=None, recipient_filter=None):
    """
    Displays and handles the ``form_class`` form to compose new messages.
    Required Arguments: None
    Optional Arguments:
        ``recipient``: username of a `django.contrib.auth` User, who should
                       receive the message, optionally multiple usernames
                       could be separated by a '+'
        ``form_class``: the form-class to use
        ``template_name``: the template to use
        ``success_url``: where to redirect after successfull submission
    """
    tokenized_recipients = None
    if request.method == "POST":
        form = form_class(request.POST, recipient_filter=recipient_filter)
        if form.is_valid():
            form.save(sender=request.user)
            messages.info(request, _(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_inbox')
            if 'next' in request.GET:
                success_url = request.GET['next']
            return HttpResponseRedirect(success_url)
    else:
        sender = request.user
        if sender:
            sender_username = sender.username
        form = form_class()
        recipient = request.GET.get('recipient',None)
        if recipient is not None:
            if ' ' in recipient:
                splitted = recipient.split(' ')
            else:
                splitted = recipient.split('+')
        body = request.GET.get('body', None)
        subject = request.GET.get('subject', None)
        if recipient is not None:
            userlist = []
            for r in splitted:
                if r.strip() != sender_username:
                    u = User.objects.filter(**{'%s' % get_username_field(): r.strip()})
                    user = u.first()
                    if user:
                        userlist.append(user)
            recipients = userlist
            tokenized_recipients = tokenize_recipients(recipients)
            # recipients = [u for u in User.objects.filter(**{'%s__in' % get_username_field(): [r.strip() for r in recipient.split('+')]})]
            form.fields['recipient'].initial = recipients
        if body is not None:
            form.fields['body'].initial = body
        if subject is not None:
            form.fields['subject'].initial = subject
    return render(request, template_name, {'form': form, 'tokenized_recipients': tokenized_recipients})
    #return render_to_response(template_name, {'form': form, 'tokenized_recipients': tokenized_recipients}, context_instance=RequestContext(request))

@login_required
def reply_w_data(request, message_id, form_class=ComposeForm,
        template_name='django_messages/compose.html', success_url=None,
        recipient_filter=None, quote_helper=format_quote,
        subject_template=_(u"Re: %(subject)s"),):
    """
    Prepares the ``form_class`` form for writing a reply to a given message
    (specified via ``message_id``). Uses the ``format_quote`` helper from
    ``messages.utils`` to pre-format the quote. To change the quote format
    assign a different ``quote_helper`` kwarg in your url-conf.

    """
    parent = get_object_or_404(Message, id=message_id)

    if parent.sender != request.user and parent.recipient != request.user:
        raise Http404

    if request.method == "POST":
        sender = request.user
        form = form_class(request.POST, recipient_filter=recipient_filter)
        if form.is_valid():
            form.save(sender=request.user, parent_msg=parent)
            messages.info(request, _(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_inbox')
            return HttpResponseRedirect(success_url)
    else:
        tokenized_recipients = tokenize_recipients([parent.sender])
        form = form_class(initial={
            'body': quote_helper(parent.sender, parent.body),
            'subject': subject_template % {'subject': parent.subject},
            'recipient': [parent.sender,]
            })
    return render(request, template_name, {'form': form, 'tokenized_recipients': tokenized_recipients})
    #return render_to_response(template_name, {'form': form,'tokenized_recipients': tokenized_recipients}, context_instance=RequestContext(request))