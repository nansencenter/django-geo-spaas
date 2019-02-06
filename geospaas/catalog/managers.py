import warnings
import pythesint as pti

from django.db import models

class SourceManager(models.Manager):

    def get_by_natural_key(self, p, i):
        return self.get(platform__category=p[0], platform__series_entity=p[1],
                platform__short_name=p[2], platform__long_name=p[3], instrument__category=i[0],
                instrument__instrument_class=i[1], instrument__type=i[2], instrument__subtype=i[3],
                instrument__short_name=i[4], instrument__long_name=i[5])

class DatasetURIQuerySet(models.QuerySet):
    def get_non_ingested_uris(self, all_uris):
        ''' Get filenames which are not in old_filenames'''
        return sorted(list(frozenset(all_uris).difference(
                            self.values_list('uri', flat=True))))

class DatasetURIManager(models.Manager):
    def get_queryset(self):
        return DatasetURIQuerySet(self.model, using=self._db)

