''' Utility functions to perform common operations '''
import urllib2
from urlparse import urlparse

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

