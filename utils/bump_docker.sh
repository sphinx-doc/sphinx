#!/bin/sh

set -ex

if [ -z "$1" ]; then
    echo "bump_docker.sh [VERSION]"
    exit
fi

cd docker
git checkout .
sed -i "" -e "s/==[0-9.]\{1,\}/==$1/" base/Dockerfile
sed -i "" -e "s/==[0-9.]\{1,\}/==$1/" latexpdf/Dockerfile
git commit -am "Bump to $1"
git tag $1
git push origin master --tags
