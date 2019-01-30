# build image geospaas (with Nansat, Django, Geo-SpaaS)
docker build -t geospaas .
# create project in the current directory
docker run --rm -v `pwd`:/code geospaas /code/init_project.sh
# remove container geospaaas (if it exists)
docker rm geospaas
# build container geospaas (with link to the current directory)
docker create -it --name=geospaas -v `pwd`:/code geospaas
