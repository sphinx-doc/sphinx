FROM python:3.8-slim-buster

# Update package listing and install security updates and
# make and pipenv

RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends make && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pipenv

# Set the working directory to our repo root
WORKDIR /sphinxtowork

# Only copy the Pipfile
COPY Pipfile Pipfile.lock /sphinxtowork/

# Install the packages
RUN pipenv install --system --deploy --python 3.9