from pathlib import Path

from geospaas.config import Settings


settings = Settings({
    'GEOSPAAS_PROCESSING_WORK_DIR': Path('/tmp/geospaas_processing'),
    'GEOSPAAS_PROCESSING_PROVIDER_SETTINGS_PATH': None,
    'GEOSPAAS_PROCESSING_FTP_HOST': None,
    'GEOSPAAS_PROCESSING_FTP_ROOT': None,
    'GEOSPAAS_PROCESSING_FTP_PATH': None,
    'GEOSPAAS_PROCESSING_PUBLISH_PREFIX': '',
    'GEOSPAAS_PROCESSING_REDIS_HOST': None,
    'GEOSPAAS_PROCESSING_REDIS_PORT': None,
})
