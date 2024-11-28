import pytest

from django.core.management import call_command

from languages_plus.utils import associate_countries_and_languages

# See: https://pytest-django.readthedocs.io/en/latest/database.html#populate-the-test-database-if-you-use-transactional-or-live-server
@pytest.fixture(scope='function')
def django_db_setup(django_db_setup, django_db_blocker):
    # NOTE: needed django_db_use_migrations to load fixtures applied in migrations
    with django_db_blocker.unblock():
        call_command('loaddata', 'languages_data.json', verbosity=0)
        call_command('update_countries_plus', verbosity=0)
        associate_countries_and_languages()