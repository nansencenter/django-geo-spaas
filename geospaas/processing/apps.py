from django.apps import AppConfig


class GeospaasProcessingConfig(AppConfig):
    name = 'geospaas.processing'
    # ensures database tables names are retro compatible
    label = "geospaas_processing"
