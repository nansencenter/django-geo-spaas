# Initialize from docker image with Python, libraries and Nansat
FROM akorosov/nansat:latest

# Install Django
RUN pip install \
    django \
    django-forms-bootstrap \
    django-leaflet

# Install Geo-SPaaS
COPY . /code
WORKDIR /code
RUN python setup.py install
