from django.conf.urls import url
from django.views.generic import RedirectView

from django_messages.views import *

urlpatterns = [
    url('', RedirectView.as_view(permanent=True, url='inbox/'), name='messages_redirect'),
    url(r'inbox/$', inbox, name='messages_inbox'),
    url(r'outbox/$', outbox, name='messages_outbox'),
    url(r'compose/$', compose, name='messages_compose'),
    url(r'compose/<recipient>/$', compose, name='messages_compose_to'),
    url(r'reply/<message_id>/$', reply, name='messages_reply'),
    url(r'view/<message_id>/$', view, name='messages_detail'),
    url(r'delete/<message_id>/$', delete, name='messages_delete'),
    url(r'undelete/<message_id>/$', undelete, name='messages_undelete'),
    url(r'trash/$', trash, name='messages_trash'),
 ]
