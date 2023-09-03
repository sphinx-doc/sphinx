FROM ghcr.io/sphinx-doc/sphinx-ci
WORKDIR /sphinxtowork
COPY . /sphinxtowork
RUN apt-get update && apt-get -y install openjdk-11-jdk-headless && rm -rf /var/lib/apt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install .[test]
RUN python3 -X dev -X warn_default_encoding -m pytest  -vv tests/test_ext_javadoctest.py --color yes --durations 25