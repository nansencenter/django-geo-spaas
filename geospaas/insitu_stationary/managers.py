import netCDF4
import warnings
from dateutil.parser import parse

from django.db import models
from django.contrib.gis.geos import GEOSGeometry

from geospaas.vocabularies.models import Platform
from geospaas.vocabularies.models import Instrument
from geospaas.vocabularies.models import DataCenter
from geospaas.vocabularies.models import Parameter
from geospaas.vocabularies.models import ISOTopicCategory
from geospaas.catalog.models import GeographicLocation
from geospaas.catalog.models import DatasetURI, Source, Dataset, DatasetParameter

# test url
# uri = https://thredds.met.no/thredds/dodsC/met.no/observations/stations/SN99938.nc
class InsituStationaryManager(models.Manager):

    def get_or_create(self, uri, *args, **kwargs):
        ''' Create dataset and corresponding metadata

        Parameters:
        ----------
            uri : str
                  URI to file or stream openable by netCDF4.Dataset
        Returns:
        -------
            dataset and flag
        '''
        # check if dataset already exists
        uris = DatasetURI.objects.filter(uri=uri)
        if len(uris) > 0:
            return uris[0].dataset, False

        try:
            nc_dataset = netCDF4.Dataset(uri)
        except OSError:
            nc_dataset = netCDF4.Dataset(uri+'#fillmismatch')

        platform = kwargs.pop('platform', '')
        instrument = kwargs.pop('instrument', '')
        if platform and instrument:
            # set source
            pp = Platform.objects.get(
                    category=platform['Category'],
                    series_entity=platform['Series_Entity'],
                    short_name=platform['Short_Name'],
                    long_name=platform['Long_Name']
                )
            ii = Instrument.objects.get(
                    category = instrument['Category'],
                    instrument_class = instrument['Class'],
                    type = instrument['Type'],
                    subtype = instrument['Subtype'],
                    short_name = instrument['Short_Name'],
                    long_name = instrument['Long_Name']
                )
            source = Source.objects.get_or_create(
                platform = pp,
                instrument = ii)[0]
        else:
            source = None

        station_name = nc_dataset.station_name
        longitude = nc_dataset.variables['longitude'][0]
        latitude = nc_dataset.variables['latitude'][0]
        location = GEOSGeometry('POINT(%s %s)' % (longitude, latitude))

        geolocation = GeographicLocation.objects.get_or_create(
                            geometry=location)[0]

        entrytitle = nc_dataset.title
        dc = DataCenter.objects.get(short_name='NO/MET')
        iso_category = ISOTopicCategory.objects.get(name='Climatology/Meteorology/Atmosphere')
        import ipdb
        ipdb.set_trace()
        summary = nc_dataset.summary

        ds = Dataset(
                entry_id = nc_dataset.id,
                entry_title = entrytitle,
                ISO_topic_category = iso_category,
                data_center = dc,
                summary = summary,
                time_coverage_start=parse(nc_dataset.time_coverage_start),
                time_coverage_end=parse(nc_dataset.time_coverage_end),
                geographic_location=geolocation)
        if source:
            ds.source = source
        ds.save()

        ds_uri = DatasetURI.objects.get_or_create(uri=uri, dataset=ds)[0]

        # Add dataset parameters
        vars = nc_dataset.variables
        time = vars.pop('time')
        lat = vars.pop('latitude')
        lon = vars.pop('longitude')
        id = vars.pop('station_id')
        for key in vars.keys():
            try:
                par = Parameter.objects.get(standard_name=vars[key].standard_name)
            except Parameter.DoesNotExist as e:
                warnings.warn('{}: {}'.format(vars[key].standard_name, e.args[0]))
                continue
            dsp = DatasetParameter(dataset=ds, parameter=par)
            dsp.save()

        return ds, True


