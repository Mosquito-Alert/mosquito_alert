# Use the official Ubuntu 20.04 image as a base
FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

ARG BUILD_ENVIRONMENT

# Install prerequisites
RUN apt-get update && apt-get install -y software-properties-common curl git

# Add Deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa

# Install Python 3.9
RUN apt-get update && apt-get install -y python3.9 python3.9-dev

# Ensure python3 points to python3.9
RUN ln -sf /usr/bin/python3.9 /usr/bin/python3

# Install uv
RUN apt-get install -y python3-setuptools
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    # https://stackoverflow.com/questions/7496547/does-python-scipy-need-blas
    gfortran libopenblas-dev liblapack-dev \
    # GIS dependencies. See: https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/geolibs/
    binutils libproj-dev gdal-bin \
    # psycopg2 dependencies
    libpq-dev

WORKDIR /app
COPY . /app

RUN uv pip install -r requirements/${BUILD_ENVIRONMENT}.txt --system

ENTRYPOINT ["/usr/bin/bash", "/app/docker-entrypoint.sh"]