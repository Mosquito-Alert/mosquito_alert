# Use the official Ubuntu 20.04 image as a base
FROM ubuntu:20.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install prerequisites
RUN apt-get update && apt-get install -y software-properties-common curl git

# Add Deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa

# Install Python 3.9
RUN apt-get update && apt-get install -y python3.9 python3.9-dev

# Ensure python3 points to python3.9
RUN ln -sf /usr/bin/python3.9 /usr/bin/python3

# Install pip for Python 3.9
RUN apt-get install -y python3-setuptools
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.9 get-pip.py
RUN rm get-pip.py

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

WORKDIR /app
COPY . /app
ENV PYTHONPATH "${PYTHONPATH}:/app/"

RUN pip install -r requirements/dev.pip

ENTRYPOINT ["/usr/bin/bash", "/app/docker-entrypoint.sh"]