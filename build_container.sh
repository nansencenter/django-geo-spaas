#!/bin/bash
# build image for running geospaas (with Python Nansat, Django, Geo-SpaaS)
docker build . -t geospaas

# set project name
PROJECT_NAME=project

# if project does not exist
if [ ! -d "$PROJECT_NAME" ]; then

    # create project in the current directory
    docker run --rm -v `pwd`:/src geospaas django-admin startproject $PROJECT_NAME

    # copy default settings
    cp tests/*.py $PROJECT_NAME/$PROJECT_NAME/
    sed -i -e 's/tests/project/g' $PROJECT_NAME/$PROJECT_NAME/settings.py

    # migrate data to database
    docker run --rm -v `pwd`:/src geospaas $PROJECT_NAME/manage.py migrate

    # add metadata to Vocabularies
    docker run --rm -v `pwd`:/src geospaas $PROJECT_NAME/manage.py update_vocabularies
fi

# remove container geospaaas (if it exists)
docker rm geospaas 2> /dev/null
# build container geospaas (mount the current directory and geospass)
docker create -it --name=geospaas \
    -v `pwd`:/src \
    geospaas
