''' Utility functions to perform common operations '''
import os
from netCDF4 import Dataset

try:
    import urllib3 as urllibN
    URLLIB_VERSION = 3
except:
    import urllib2 as urllibN
    URLLIB_VERSION = 2

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from django.conf import settings

def module_path(module, root):
    media_path = root
    for m in module.split('.'):
        media_path = os.path.join(media_path, m)
        if not os.path.exists(media_path):
            os.mkdir(media_path)
    return media_path


def path(module, filename, root):
    mp = module_path(module, root)

    # Get the path of media files created from <filename>
    basename = os.path.split(filename)[-1].split('.')[0]
    dataset_path = os.path.join(mp, basename)
    if not os.path.exists(dataset_path):
        os.mkdir(dataset_path)

    return dataset_path

def media_path(module, filename):
    return path(module, filename, settings.MEDIA_ROOT)

def product_path(module, filename):
    return path(module, filename, settings.PRODUCTS_ROOT)

def validate_uri(uri):
    """ Validation of URI and its existence

    URI conventions: URI = scheme:[//authority]path[?query][#fragment]
    
    Examples:
        file://localhost/some/path/filename.ext
        http://www.eee.rrr/some/path

    If URI is not valid, the function raises a ValueError or urrlib error

    """
    validation_result = False
    uri_parts = urlparse(uri)
    if uri_parts.scheme=='file' and uri_parts.netloc=='localhost':
        if not os.path.isfile(uri_parts.path):
            raise FileNotFoundError(uri_parts.path)
    else:
        if URLLIB_VERSION == 2:
            request = urllibN.Request(uri)
        else:
            request = urllibN.PoolManager(cert_reqs='CERT_NONE').request('GET', uri)
        if not request.status==200:
            try:
                ds = Dataset(uri)
            except OSError:
                ds = Dataset(uri+'#fillmismatch')


def nansat_filename(uri):
    # Check if data should be read as stream or as file? Or just:
    # open with Nansat
    uri_content = urlparse(uri)
    if uri_content.scheme=='file':
        return uri_content.path
    elif uri_content.scheme=='ftp':
        return urllib.urlretrieve(uri)[0]
    else:
        return uri

def uris_from_args(fnames):
    if len(fnames[0].split(':'))==1:
        uris = ['file://localhost' + fn for fn in fnames]
    else:
        uris = [uri for uri in fnames]
    return uris

