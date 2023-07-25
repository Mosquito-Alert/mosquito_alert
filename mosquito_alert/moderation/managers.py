from django.db.models import Manager

from .querysets import FlagModeratedQueryset

FlagModeratedManager = Manager.from_queryset(FlagModeratedQueryset)
