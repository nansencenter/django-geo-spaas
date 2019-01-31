# build image geospaas (with Nansat, Django, Geo-SpaaS)
docker build . -t geospaas --build-arg DUID=10147 --build-arg DGID=15001

# set project name
PROJECT_NAME=project

# if project does not exist
if [ ! -d "$PROJECT_NAME" ]; then

    # create project in the current directory
    docker run --rm -v `pwd`:/django-geo-spaas geospaas django-admin startproject $PROJECT_NAME /django-geo-spaas

    # copy default settings
    cp tests/*.py $PROJECT_NAME/$PROJECT_NAME/

    # migrate data to database
    docker run --rm -v `pwd`:/django-geo-spaas geospaas python /django-geo-spaas/$PROJECT_NAME/manage.py migrate

    # add metadata to Vocabularies
    docker run --rm -v `pwd`:/django-geo-spaas geospaas python /django-geo-spaas/$PROJECT_NAME/manage.py update_vocabularies
fi

# remove container geospaaas (if it exists)
docker rm geospaas 2> /dev/null
# build container geospaas (with link to the current directory)
docker create -it --name=geospaas -v `pwd`:/django-geo-spaas geospaas
