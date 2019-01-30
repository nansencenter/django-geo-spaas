FROM nansat:latest

RUN pip install \
    django \
    django-forms-bootstrap \
    django-leaflet

COPY . /code
WORKDIR /code
RUN python setup.py install
