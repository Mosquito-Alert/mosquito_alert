from unittest.mock import patch

import pytest
from django.db import transaction
from django.db.utils import DEFAULT_DB_ALIAS, ConnectionHandler, OperationalError


def func_in_race_condition_test(obj, func, validation_func):
    # IMPORTANT: all functions calling this must have the decorator @pytest.mark.django_db(transaction=True)
    with transaction.atomic():
        func()

        # Mock a new connection (e.g. from another server)
        new_connection = ConnectionHandler().create_connection(alias=DEFAULT_DB_ALIAS)
        with patch("django.db.utils.ConnectionHandler.__getitem__") as mock:
            mock.return_value = new_connection

            # The first transaction has NOT been committed
            # before we begin the second, so the lock is still in effect.
            # Using nowait = True, to raise if row is blocked.
            with transaction.atomic():
                # Checking that the row is locked. Nobody can update.
                with pytest.raises(OperationalError):
                    _ = obj.__class__.objects.select_for_update(nowait=True).get(pk=obj.pk)

    assert validation_func()

    # TODO: not sure if this makes sense in race condition.
    # Mock a new connection (e.g. from another server)
    # new_connection = ConnectionHandler().create_connection(alias=DEFAULT_DB_ALIAS)
    # with patch("django.db.utils.ConnectionHandler.__getitem__") as mock:
    #     mock.return_value = new_connection
    #     # The first transaction has been committed
    #     # before we begin the second, so the lock has been released.
    #     with transaction.atomic():
    #         func()

    # assert getattr(obj, field_name) == inital_value + 2 * inc_value
