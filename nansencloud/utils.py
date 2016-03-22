''' Utility functions to perform common operations '''
import os
import urllib2
from urlparse import urlparse
from django.conf import settings

def module_media_path(module):
    media_path = settings.MEDIA_ROOT
    for m in module.split('.'):
        media_path = os.path.join(media_path, m)
        if not os.path.exists(media_path):
            os.mkdir(media_path)
    return media_path


def media_path(module, filename):

    # Check that the file exists
    if not os.path.exists(filename):
        raise IOError('%s: File does not exist' %filename)

    media_path = module_media_path(module)

    # Get the path of media files created from <filename>
    basename = os.path.split(filename)[-1].split('.')[0]
    dataset_media_path = os.path.join(media_path, basename)
    if not os.path.exists(dataset_media_path):
        os.mkdir(dataset_media_path)

    return dataset_media_path

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

