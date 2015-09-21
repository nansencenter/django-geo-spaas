from django.contrib.gis.db import models

from noaa_ndbc.managers import StdMetMeasurementManager


class StandarMeteorologicalBuoy(models.Model):
    ndbc_id = models.CharField(max_length=5)
    location = models.PointField()

    objects = models.GeoManager()

    def get_opendap_url(self, year):
        base = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/stdmet/'
        return base+self.ndbc_id+'/'+self.ndbc_id+'h'+str(year)+'.nc'

    def temporal_search(self):
        pass

class StdMetMeasurement(models.Model):
    buoy = models.ForeignKey(StandardMeteorologicalBuoy)
    time = models.DateTimeField()
    wind_from_direction = models.FloatField()
    wind_speed = models.FloatField()
    gust = models.FloatField()
    wave_height = models.FloatField()
    dominant_wave_period = models.FloatField()
    # etc...

    objects = StdMetMeasurementManager()
