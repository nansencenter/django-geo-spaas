''' Utility functions to perform common operations '''
import os

try:
    import urllib3 as urllibN
    URLLIB_VERSION = 3
except:
    import urllib2 as urllibN
    URLLIB_VERSION = 2

try:
    from urlparse import urlparse
except ImportError:
    import urllib.parse as urlparse

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
    return path(module, filename, settings.PRODUCTS_ROOT)

def validate_uri(uri):
    validation_result = False
    request = urllib2.Request(uri)
    try:
        if URLLIB_VERSION == 2:
            request = urllibN.Request(uri)
        else:
            request = urllibN.PoolManager().request('GET', uri)
            response.close()
        validation_result = True
    except IOError as e:
        if len(e.args)>1 and e.args[1]==u'Is a directory':
            validation_result = True
    return validation_result

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

