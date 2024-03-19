# main purpose of this file is to have a recipe about how to run java doc test into docker engine
# 1. cd $PWD/sphinx/sphinx
# 2. Run the Sphinx Java test: docker build . -t sphinx-java-ext -f tests/roots/test-ext-javadoctest/Dockerfile
FROM ghcr.io/sphinx-doc/sphinx-ci
WORKDIR /sphinxtowork
COPY . /sphinxtowork
RUN apt-get update && apt-get -y install maven openjdk-11-jdk-headless && rm -rf /var/lib/apt
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install .[test]
RUN python3 -X dev -X warn_default_encoding -m pytest  -vv tests/test_ext_javadoctest.py --color yes --durations 25
