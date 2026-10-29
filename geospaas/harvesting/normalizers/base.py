"""Module containing the base class for GeoSPaaS normalizers"""
import concurrent.futures
import logging
import os
import pickle
import queue
import threading
from datetime import datetime
from pathlib import Path

import geospaas.harvesting.normalizers.utils as utils
from geospaas.harvesting.config import settings


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class MetadataNormalizer():
    """Base class for all metadata normalizers"""

    name = None
    can_force = ['location', 'time_coverage_start', 'time_coverage_end']

    def __init__(self, **kwargs):
        self.logger = logging.getLogger(f"geospaas.harvesting.normalizers.{self.name}")
        self.extra_tags = kwargs.get('tags', {})
        self.max_threads = kwargs.get('max_threads', 1)
        self.force = {}
        for key in self.can_force:
            force_value = kwargs.get(key)
            if force_value is not None:
                self.force[key] = force_value

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(tags={self.extra_tags}, max_threads={self.max_threads})"

    def normalize(self, dataset_info):
        """Takes a DatasetInfo object and returns the necessary
        arguments to instantiate a Dataset, DatasetURI and the
        associated keywords, parameters and tags
        """
        dataset_kwargs = {
            'time_coverage_start': (self.force.get('time_coverage_start')
                                    or self.get_time_coverage_start(dataset_info)),
            'time_coverage_end': (self.force.get('time_coverage_end')
                                  or self.get_time_coverage_end(dataset_info)),
            'location': (self.force.get('location')
                         or self.get_location_geometry(dataset_info)),
            'entry_title': self.get_entry_title(dataset_info),
            'summary': self.get_summary(dataset_info),
        }
        # entry_id should not be in the arguments if a value could not
        # be found because it would interfere with generating a default
        # value
        entry_id = self.get_entry_id(dataset_info)
        if entry_id:
            dataset_kwargs['entry_id'] = entry_id

        keywords = self.get_keywords(dataset_info)
        parameters = self.get_dataset_parameters(dataset_info)
        tags_kwargs = self._get_all_tags(dataset_info)
        extra_urls = self.get_extra_urls(dataset_info)
        return (dataset_kwargs, [dataset_info.url, *extra_urls], keywords, parameters, tags_kwargs)

    def normalize_stream(self, dataset_infos):
        """Normalize an iterable of DatasetInfo objects.
        """
        return StreamMetadataNormalizer(self, dataset_infos)

    def get_entry_id(self, dataset_info):
        """Get the entry ID from the raw metadata"""
        raise NotImplementedError

    def get_time_coverage_start(self, dataset_info):
        """Get the start of the time coverage from the raw metadata"""
        raise NotImplementedError

    def get_time_coverage_end(self, dataset_info):
        """Get the end of the time coverage from the raw metadata"""
        raise NotImplementedError

    def get_location_geometry(self, dataset_info):
        """Get the location geometry (in WKT or GeoJSON) from the raw
        metadata
        """
        raise NotImplementedError

    def get_entry_title(self, dataset_info):
        """Get the entry title from the raw metadata"""
        return ''

    def get_summary(self, dataset_info):
        """Get the summary from the raw metadata"""
        return ''

    def get_keywords(self, dataset_info):
        """Find relevant keywords"""
        return []

    def _get_all_tags(self, dataset_info):
        """Get tags from the dataset_info and manually specified at the
        Normalizer level
        """
        # initialize list with forced tags
        tags_kwargs = [
            {'name': key, 'value': value}
            for key, value in self.extra_tags.items()
        ]
        # add tags retrieved from dataset metadata
        tags_kwargs.extend(self.get_tags(dataset_info))
        return tags_kwargs

    def get_tags(self, dataset_info):
        """Find relevant tags. Returns a list of dicts of arguments
        used to instantiate Tag objects
        """
        return []

    def get_dataset_parameters(self, dataset_info):
        """Get the dataset's parameters, if any, from the raw metadata
        Note that if a parameter is not found in the database, no error is
        raised, but a warning is logged
        """
        try:
            return utils.create_parameter_list(dataset_info.metadata['raw_dataset_parameters'])
        except KeyError:
            return []

    def get_extra_urls(self, dataset_info):
        """Get extra URLs for the dataset (for example alternative
        download URLs)
        """
        return []


class Stop():
    """Class used in normalizing queues to signal that processing
    should stop
    """


class StreamMetadataNormalizer():
    """"""
    logger = logging.getLogger(__name__ + '.StreamMetadataNormalizer')
    QUEUE_SIZE = 500
    FAILED_INGESTIONS_PATH = settings.GEOSPAAS_HARVESTING_FAILED_INGESTIONS_PATH
    MAX_FAILED = 500000  # max number of failed objects per recovery file
    RECOVERY_SUFFIX = 'failed_ingestions.pickle'

    def __init__(self, normalizer, dataset_infos):
        """Creates a managing thread which will in turn spawn
        normalization threads
        """
        self.dataset_infos = dataset_infos
        self.normalizer = normalizer
        self._results = None
        self._failed = None
        self._started = False
        self.main_thread = None
        self.manager_thread = None

    def __del__(self):
        """Make sure the managing thread is done
        """
        if self.main_thread == threading.current_thread():
            if self.manager_thread is not None:
                self.manager_thread.join()

    def __iter__(self):
        if not self._started:
            self._results = queue.Queue(self.QUEUE_SIZE)
            self._failed = queue.Queue(self.QUEUE_SIZE)
            self.main_thread = threading.current_thread()
            self.manager_thread = threading.Thread(target=self._start_normalizing, daemon=True)
            self.manager_thread.start()
            self._started = True
        return self

    def __next__(self):
        """Gets the next result from the _results queue"""
        next_result = self._results.get()
        if next_result is Stop:
            raise StopIteration()
        else:
            return next_result

    def _pickle_list_elements(self, list_to_pickle, pickle_path):
        """Pickle all the elements in the list, then empty it"""
        self.logger.info("Dumping items to %s", pickle_path)
        with open(pickle_path, 'ab') as pickle_file:
            for element_to_pickle in list_to_pickle:
                pickle.dump(element_to_pickle, pickle_file)
        list_to_pickle.clear()

    def _start_normalizing(self, **kwargs):
        """Iterate over the DatasetInfo objects obtained from the
        DatasetInfo iterator and normalize the attributes. Normalizing
        happens in separate threads to parallelize the I/Os.
        """
        # Launch thread which checks the size of the failed ingestions
        # queue and dumps it to disk when necessary
        self.logger.debug("Starting normalizing failure management thread for %s",
                          self.normalizer.name)
        failed_queue_thread = threading.Thread(target=self._thread_manage_failed_normalizing)
        failed_queue_thread.start()
        self.logger.debug("Starting normalizer threads for %s (max %s)",
                          self.normalizer.name, self.normalizer.max_threads)
        try:
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.normalizer.max_threads,
                    thread_name_prefix=self.__class__.__name__) as executor:
                futures = []
                for dataset_info in self.dataset_infos:
                    self.logger.debug("Normalizing %s", dataset_info)
                    futures.append(executor.submit(
                        self._thread_normalize,
                        dataset_info,
                        **kwargs
                    ))
        except KeyboardInterrupt:
            self.logger.info('Normalizing thread received stopping signal')
            for future in reversed(futures):
                future.cancel()
            self.logger.info(
                'Cancelled future normalizing threads')
        except Exception as error:
            self.logger.error('Unexpected error happened during normalizing', exc_info=True)
        finally:
            self.logger.debug("Stopping normalizing threads")
            self._results.put(Stop)
            self.logger.debug('Stopping failed queue watcher thread')
            self._failed.put(Stop)
            failed_queue_thread.join()

            # raise exceptions from threads
            for future in concurrent.futures.as_completed(futures):
                exception = future.exception()
                if exception:
                    self.logger.error(
                        "Exception happened during thread",
                        exc_info=exception)

    def _thread_normalize(self, dataset_info, **kwargs):
        """
        Gets the attributes needed to insert a dataset into the
        database from its URL, and puts a dictionary containing these
        attributes in the results queue.
        If an error occurs while retrieving the attributes, the dataset
        info and the exception are put in the _failed queue for
        processing by the dedicated thread.
        This method is meant to be run in a thread.
        """
        self.logger.debug("Getting metadata for '%s'", dataset_info.url)
        try:
            result = self.normalizer.normalize(dataset_info, **kwargs)
        except Exception as error:  # pylint: disable=broad-except
            self.logger.error("Could not get metadata for '%s'", dataset_info.url, exc_info=True)
            self._failed.put((dataset_info, error), block=True)
        else:
            self._results.put(result)

    def _thread_manage_failed_normalizing(self):
        """Watches the `_failed` queue and put the incoming failed
        elements in a list. When the list reaches its maximum size or
        when None is received, dump the contents of the list to a file.
        This method is meant to be run in a thread.
        """
        try:
            self.logger.debug("Failure management thread started")
            class_name = self.__class__.__name__.lower()
            date = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')
            pickle_path = Path(self.FAILED_INGESTIONS_PATH,
                            f'{class_name}_{date}_{self.RECOVERY_SUFFIX}')

            os.makedirs(self.FAILED_INGESTIONS_PATH, exist_ok=True)

            failed_ingestions = []
            while True:
                element = self._failed.get()

                if element is Stop:
                    self.logger.debug("Stopping failure management thread")
                    if failed_ingestions:
                        self._pickle_list_elements(failed_ingestions, pickle_path)
                    self._failed.task_done()
                    break

                failed_ingestions.append(element)
                if len(failed_ingestions) >= self.MAX_FAILED:
                    self._pickle_list_elements(failed_ingestions, pickle_path)
                self._failed.task_done()
        except Exception as e:
            self.logger.error('Error happened in failure management thread', exc_info=e)
