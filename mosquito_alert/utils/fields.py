import math
import secrets
from typing import Any

from django.apps import apps
from django.db import models
from simple_history.models import HistoricalRecords, registered_models


class ProxyAwareHistoricalRecords(HistoricalRecords):
    """
    This specialized HistoricalRecords model field is to be used specifically for
    tracking history on instances of proxy models.
    Set `history = ProxyAwareHistoricalRecords(inherit=True) on the parent (concrete) model,
    and proxy models that subclass the parent will have their history tracked in the history
    table of the parent.
    The only downside is that this seems to cause no-op migrations to be created for each
    proxy model (as opposed to no migration at all).
    The migration defines a historical table for the proxy model with no fields, which sqlmigrate
    translates to an empty transaction: `BEGIN; COMMIT;`.
    Copied verbatim from https://github.com/jazzband/django-simple-history/issues/544#issuecomment-1538615799
    """

    def _find_base_history(self, opts):
        base_history = None
        for parent_class in opts.parents.keys():
            if hasattr(parent_class, "history"):
                base_history = parent_class.history.model
        return base_history

    def create_history_model(self, model, inherited):
        opts = model._meta
        if opts.proxy:
            base_history = self._find_base_history(opts)
            if base_history:
                return self.create_proxy_history_model(model, inherited, base_history)

        return super().create_history_model(model, inherited)

    def create_proxy_history_model(self, model, inherited, base_history):
        opts = model._meta
        attrs = {
            "__module__": self.module,
            "_history_excluded_fields": self.excluded_fields,
        }
        app_module = f"{opts.app_label}.models"
        if inherited:
            attrs["__module__"] = model.__module__
        elif model.__module__ != self.module:
            # registered under different app
            attrs["__module__"] = self.module
        elif app_module != self.module:
            # Abuse an internal API because the app registry is loading.
            app = apps.app_configs[opts.app_label]
            models_module = app.name
            attrs["__module__"] = models_module

        attrs.update(Meta=type("Meta", (), {**self.get_meta_options(model), "proxy": True}))
        if self.table_name is not None:
            attrs["Meta"].db_table = self.table_name

        name = self.get_history_model_name(model)
        registered_models[opts.db_table] = model
        return type(str(name), (base_history,), attrs)


class ShortIDField(models.CharField):
    """
    A custom model field that generates a short, URL-safe identifier.
    """

    def __init__(self, size: int, *args, **kwargs) -> None:
        if not isinstance(size, int) or size <= 0:
            raise ValueError("Size must be a positive integer.")
        # See: https://zelark.github.io/nano-id-cc/
        self.size = size
        kwargs["max_length"] = size  # Assign max_length from size
        kwargs["default"] = self.generate_short_id  # Use the method to generate the default value
        super().__init__(*args, **kwargs)

    def generate_short_id(self):
        """Generates a URL-safe short ID of specified length."""
        return secrets.token_urlsafe(nbytes=math.ceil(self.size / 1.3))[: self.size]

    def deconstruct(self) -> Any:
        name, path, args, kwargs = super().deconstruct()
        kwargs["size"] = self.size
        del kwargs["max_length"]
        del kwargs["default"]
        return name, path, args, kwargs
