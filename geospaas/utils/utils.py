''' Utility functions to perform common operations '''
import os
import urllib
import urllib.request
from urllib.parse import urlparse

import netCDF4
from django.conf import settings


def validate_uri(uri):
    """ Validation of URI and its existence

    URI conventions: URI = scheme:[//authority]path[?query][#fragment]

    Examples:
        file://localhost/some/path/filename.ext
        http://www.eee.rrr/some/path

    If URI is not valid, the function raises a ValueError or urrlib error

    """
    uri_parts = urlparse(uri)
    if uri_parts.scheme=='file' and uri_parts.netloc=='localhost':
        if not os.path.isfile(uri_parts.path):
            raise FileNotFoundError(uri_parts.path)
    else:
        response = urllib.request.urlopen(uri)
        if not response.status==200:
            try:
                netCDF4.Dataset(uri)
            except OSError:
                netCDF4.Dataset(uri+'#fillmismatch')


def nansat_filename(uri):
    # Check if data should be read as stream or as file? Or just:
    # open with Nansat
    uri_content = urlparse(uri)
    if uri_content.scheme=='file':
        return uri_content.path
    elif uri_content.scheme=='ftp':
        return urllib.request.urlretrieve(uri)[0]
    else:
        return uri
