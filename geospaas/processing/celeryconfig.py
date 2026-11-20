# """ Celery settings"""
# import os

# from geospaas.processing.config import settings


# broker_url = settings.GEOSPAAS_PROCESSING_BROKER
# result_backend = 'django-db'
# accept_content = ['json', 'pickle']
# task_routes = {
#     'geospaas.processing.tasks.core.*': {'queue': 'core'},
#     'geospaas.processing.tasks.idf.*': {'queue': 'idf'},
#     'geospaas.processing.tasks.syntool.*': {'queue': 'syntool'},
#     'geospaas.processing.tasks.harvesting.*': {'queue': 'harvesting'},
# }
# worker_prefetch_multiplier = '1'

# result_backend_always_retry = True
# result_backend_max_retries = 10
