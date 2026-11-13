"""Tasks for harvesting data"""
import os

import celery
import celery.utils

from geospaas.harvesting.cli import refresh_vocabularies, retry_ingest
import geospaas.harvesting.providers as providers

from geospaas.processing.celery import app, GeoSPaaSTask


logger = celery.utils.log.get_task_logger(__name__)


HARVEST_CONFIG_PATH = os.getenv('GEOSPAAS_PROCESSING_HARVEST_CONFIG')


@app.task(base=GeoSPaaSTask, bind=True, track_started=True)
def start_harvest(self, search_config_dict):
    """Launch harvesting according to the search configuration"""
    search_config = providers.SearchConfiguration.from_dict(search_config_dict)
    searches = search_config.create_provider_searches()
    logger.info("Running the following searches: %s", searches)
    tasks_to_run = celery.group(
        save_search_results.s(search_results)
        for search_results in searches
    ) | retry_ingestion.si()

    results = tasks_to_run.apply_async(queue='harvesting')
    logger.info("results %s", results)


@app.task(base=GeoSPaaSTask, bind=True, track_started=True, serializer='pickle')
def save_search_results(self, search_results):
    """Write search results to the GeoSPaaS database"""
    search_results.save()


@app.task(base=GeoSPaaSTask, bind=True, track_started=True)
def update_vocabularies(self):
    """Update vocabularies in the GeoSPaaS database"""
    refresh_vocabularies()


@app.task(base=GeoSPaaSTask, bind=True, track_started=True)
def retry_ingestion(self):
    """Retry failed ingestions. Requires the
    GEOSPAAS_FAILED_INGESTIONS_DIR environment variables to be set (see
    geospaas.harvesting.recovery for more details)
    """
    retry_ingest()
