# define an alias for the specfic python version used in this file.
FROM python:3.11.4-slim-bullseye as python

# Python build stage
FROM python as python-build-stage

ARG BUILD_ENVIRONMENT

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    # install git (remove if not requirement needs to be installed using git)
    git \
    # dependencies for building Python packages
    build-essential \
    # psycopg2 dependencies
    libpq-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN pip wheel --wheel-dir /usr/src/app/wheels  \
    -r ${BUILD_ENVIRONMENT}.txt

# Python 'run' stage
FROM python as python-run-stage

LABEL org.opencontainers.image.source=https://github.com/Mosquito-Alert/mosquito_alert
LABEL org.opencontainers.image.licenses=gpl-3.0

ARG BUILD_ENVIRONMENT
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django django

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    # Needed for docker healthcheck
    curl \
    # psycopg2 dependencies
    libpq-dev \
    # Translations dependencies
    gettext \
    # GIS dependencies. See: https://docs.djangoproject.com/en/4.1/ref/contrib/gis/install/geolibs/
    binutils libproj-dev gdal-bin \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
    && rm -rf /wheels/


COPY --chown=django:django ./docker-entrypoint.sh /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint


COPY --chown=django:django ./compose/${BUILD_ENVIRONMENT}/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start
COPY --chown=django:django ./compose/${BUILD_ENVIRONMENT}/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker


COPY --chown=django:django ./compose/${BUILD_ENVIRONMENT}/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat


COPY ./compose/${BUILD_ENVIRONMENT}/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower


# copy application code to WORKDIR
COPY --chown=django:django . ${APP_HOME}

# make django owner of the WORKDIR directory as well.
RUN chown django:django ${APP_HOME}

USER django

RUN DATABASE_URL="" \
    CELERY_BROKER_URL="" \
    DJANGO_SETTINGS_MODULE="config.settings.test" \
    python manage.py compilemessages

ENTRYPOINT ["/entrypoint"]
