import warnings
import pythesint as pti

from django.db import models

DAP_SERVICE_NAME = 'dapService'
OPENDAP_SERVICE = 'OPENDAP'
FILE_SERVICE_NAME = 'fileService'
LOCAL_FILE_SERVICE = 'local'
HTTP_SERVICE_NAME = 'http'
HTTP_SERVICE = 'HTTPServer'
WMS_SERVICE_NAME = 'wms'
WMS_SERVICE = 'WMS'

class SourceManager(models.Manager):

    def get_by_natural_key(self, p, i):
        return self.get(platform__short_name=p, instrument__short_name=i)

class DatasetURIQuerySet(models.QuerySet):
    def get_non_ingested_uris(self, all_uris):
        ''' Get filenames which are not in old_filenames'''
        return sorted(list(frozenset(all_uris).difference(
                            self.values_list('uri', flat=True))))

class DatasetURIManager(models.Manager):
    def get_queryset(self):
        return DatasetURIQuerySet(self.model, using=self._db)

