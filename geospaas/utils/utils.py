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
