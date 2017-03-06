''' Utility functions to perform common operations '''
import os
import urllib2
from urlparse import urlparse
from django.conf import settings

def module_path(module, root):
    for m in module.split('.'):
        media_path = os.path.join(root, m)
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
    return path(module, filename, settings.PRODUCT_ROOT)

def validate_uri(uri):
    request = urllib2.Request(uri)
    response = urllib2.urlopen(request)
    response.close()

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

def uris_from_args(*args):
    if len(args[0].split(':'))==1:
        uris = ['file://localhost' + fn for fn in args]
    else:
        uris = [uri for uri in args]
    return uris

