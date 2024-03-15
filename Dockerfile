# Use the official Ubuntu 20.04 image as a base
FROM ubuntu:20.04

# Update package list
RUN apt-get update

# Install prerequisites
RUN apt-get install -y software-properties-common

# Add Deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa

# Update package list again
RUN apt-get update

# Install Python 3.8.10
RUN apt-get install -y python3.8 python3-pip

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
    # https://stackoverflow.com/questions/7496547/does-python-scipy-need-blas
    gfortran libopenblas-dev liblapack-dev \
    # GIS dependencies. See: https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/geolibs/
    binutils libproj-dev gdal-bin \
    # psycopg2 dependencies
    libpq-dev \
    # For matplotlib
    pkg-config libfreetype6-dev

# Install dependencies
#     setuptools<58.0.0 required for anyjson
#     cython<3.0.0 required for the pyyaml version we are using (https://stackoverflow.com/questions/7496547/does-python-scipy-need-blas)
RUN pip install --upgrade pip "setuptools<58.0.0" "wheel==0.40.0" "cython<3.0.0"
# Solved bug when install scikit. Use same version as dev.pip
RUN pip install numpy==1.23.1

WORKDIR /app
COPY . /app
ENV PYTHONPATH "${PYTHONPATH}:/app/"

RUN pip install -r requirements/dev.pip

ENTRYPOINT ["/usr/bin/bash", "/app/docker-entrypoint.sh"]