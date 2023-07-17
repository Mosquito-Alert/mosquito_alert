import pytest
from django.db import connection
from django.db.utils import ProgrammingError

from .models import (
    DummyAL_NodeParentManageableModel,
    DummyMP_NodeExpandedQueriesModel,
    DummyMP_NodeParentManageableModel,
    DummyMPModel,
    DummyNS_NodeParentManageableModel,
)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    def create_model(model):
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(model)
        except ProgrammingError:
            pass

    with django_db_blocker.unblock():
        create_model(model=DummyMPModel)
        create_model(model=DummyMP_NodeParentManageableModel)
        create_model(model=DummyAL_NodeParentManageableModel)
        create_model(model=DummyNS_NodeParentManageableModel)
        create_model(model=DummyMP_NodeExpandedQueriesModel)

    yield

    with django_db_blocker.unblock():
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyMPModel)
            schema_editor.delete_model(DummyMP_NodeParentManageableModel)
            schema_editor.delete_model(DummyAL_NodeParentManageableModel)
            schema_editor.delete_model(DummyNS_NodeParentManageableModel)
            schema_editor.delete_model(DummyMP_NodeExpandedQueriesModel)
