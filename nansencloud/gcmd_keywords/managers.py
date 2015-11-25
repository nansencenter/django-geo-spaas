#-------------------------------------------------------------------------------
# Name:
# Purpose:      
#
# Author:       Morten Wergeland Hansen
# Modified:
#
# Created:
# Last modified:
# Copyright:    (c) NERSC
# License:      
#-------------------------------------------------------------------------------
import os, json
from nerscmetadata import gcmd_keywords

from django.db import models

class PlatformManager(models.Manager):

    def create_from_gcmd_keywords(self):
        #platforms = json.load(open(json_fn))['Platforms']
        ## 'Category', 'Series_Entity', 'Short_Name', 'Long_Name'
        #for category in platforms.keys():
        #    if category=='Revision':
        #        continue
        #    for series_entity in platforms[category].keys():
        #        for short_and_long_names in platforms[category][series_entity]:
        #            pp, created = self.get_or_create(
        #                category = category,
        #                series_entity = series_entity,
        #                short_name = short_and_long_names[0],
        #                long_name = short_and_long_names[1]
        #            )
        num = 0
        for p in gcmd_keywords.get_keywords('Platforms', update=True):
            pp, created = self.get_or_create(
                    category=p[0], 
                    series_entity=p[1],
                    short_name=p[2], 
                    long_name=p[3])
            if created: num+=1
        print("Successfully added %d new platforms" %num)

class InstrumentManager(models.Manager):

    def create_from_gcmd_keywords(self):
        # 'Category', 'Class', 'Type', 'Subtype', 'Short_Name', 'Long_Name'
        num = 0
        for ins in gcmd_keywords.get_keywords('Instruments', update=True):
            ii, created = self.get_or_create(
                    category=ins[0], 
                    instrument_class=ins[1], 
                    type=ins[2],
                    subtype=ins[3], 
                    short_name=ins[4], 
                    long_name=ins[5])
            if created: num+=1
        print("Successfully added %d new instruments" %num)

        #instruments = json.load(open(json_fn))['Instruments']
        #for category in instruments.keys():
        #    if category=='Revision':
        #        continue
        #    for iclass in instruments[category].keys():
        #        for type in instruments[category][iclass].keys():
        #            for subtype in instruments[category][iclass][type].keys():
        #                for short_and_long_names in instruments[category][iclass][type][subtype]:
        #                    ii, created = self.get_or_create(
        #                        category = category,
        #                        instrument_class = iclass,
        #                        type = type,
        #                        subtype = subtype,
        #                        short_name = short_and_long_names[0],
        #                        long_name = short_and_long_names[1]
        #                    )
