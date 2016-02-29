import warnings
import pythesint as pti

from django.db import models

class SourceManager(models.Manager):

    def get_by_natural_key(self, p, i):
        return self.get(platform__short_name=p, instrument__short_name=i)

class ParameterManager(models.Manager):

    ''' Fields:
    standard_name
    short_name
    units 
    gcmd_science_keyword 
    '''

    def get_by_natural_key(self, stdname):
        return self.get(standard_name=stdname)

    def create_from_standards(self):
        ''' Create parameter instances from the nersc wkv list.
        '''
        warnings.warn('''
        Because we do not yet have the mapping between the different
        vocabularies, the GCMD science keywords are not linked to the catalog
        parameter table
        ''')
        num = 0
        pti.update_wkv_variable()
        for wkv in pti.get_wkv_variable_list():
            pp, created = self.get_or_create(
                standard_name = wkv['standard_name'],
                short_name = wkv['short_name'],
                units = wkv['units']
            )
            if created: num+=1
        print("Added %d new parameters" %num)
