from django.db import models
from django.core.exceptions import ValidationError

from geospaas.vocabularies.managers import KeywordManager, ParameterManager


# GCMD keywords loaded into the models in migrations/0001_initial.py using the
# nersc-metadata package

class Keyword(models.Model):
    """"""
    version = models.CharField(max_length=100, blank=True, null=True)
    kind = models.CharField(max_length=100, null=False)
    data = models.JSONField(null=False)

    objects = KeywordManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_keyword', fields=('version', 'kind', 'data'))
        ]


def validate_parameter(value):
    """Validate that a parameter has a 'standard_name' attribute
    """
    if not (isinstance(value, dict) and 'standard_name' in value):
        raise ValidationError


class Parameter(models.Model):
    ''' Standard name (and unit) is taken from the CF variables but in case a
    geophysical parameter is not in the CF standard names table it needs to be
    taken from wkv.xml (in nansat).

    Short name is taken from wkv.xml

    The table should also include the relevant GCMD science keyword
    '''
    version = models.CharField(max_length=100, blank=True, null=True)
    kind = models.CharField(max_length=100, blank=True, null=True)
    data = models.JSONField(unique=True, validators=(validate_parameter,))

    # The science keywords are less specific than the CF standard names -
    # therefore one science keyword can be in many parameters, whereas the
    # CF/WKV standard names are unique
    gcmd_science_keyword = models.ForeignKey(
        Keyword, blank=True, null=True, on_delete=models.CASCADE)

    objects = ParameterManager()

    def __str__(self):
        return str(self.data['standard_name'])

    def natural_key(self):
        return (self.data['standard_name'])

    class Meta:
        constraints = [
            models.UniqueConstraint(name='unique_parameter', fields=('version', 'kind', 'data'))
        ]
