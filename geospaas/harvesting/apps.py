from django.apps import AppConfig


class GeoSPaaSHarvestingConfig(AppConfig):
    name = "geospaas.harvesting"
    # ensures database tables names are retro compatible
    label = "geospaas_harvesting"
