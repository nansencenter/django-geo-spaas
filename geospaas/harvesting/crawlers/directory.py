import calendar
import ftplib
import functools
import io
import itertools
import logging
import os
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta, timezone

import netCDF4
import numpy as np
import shapely.wkt
from nansat import Nansat
from geospaas.utils.utils import nansat_filename
from shapely.geometry import MultiPoint

import geospaas.harvesting.arguments as arguments
from .base import Crawler, DatasetInfo


class LinkExtractor(HTMLParser):
    """
    HTML parser which extracts links from an HTML page
    """

    logger = logging.getLogger(__name__ + '.LinkExtractor')

    def __init__(self):
        """Constructor with extra attribute definition"""
        super().__init__()
        self._links = []

    def error(self, message):
        """Error behavior"""
        self.logger.error(message)

    def feed(self, data):
        """Reset links lists when new data is fed to the parser"""
        self._links = []
        super().feed(data)

    @property
    def links(self):
        """Getter for the links attribute"""
        return self._links

    def handle_starttag(self, tag, attrs):
        """Extracts links from the HTML data"""
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href':
                    self._links.append(attr[1])


class DirectoryCrawler(Crawler):
    """Parent class for crawlers used on repositories which expose a directory-like structure"""
    name = None
    argument_parser = arguments.ArgumentParser([
        *Crawler.argument_parser.arguments.values(),
        arguments.StringArgument('url', required=True),
        arguments.StringArgument('include', default=None),
    ])

    EXCLUDE = None

    YEAR_PATTERN = r'y?(?P<year>\d{4})'
    MONTH_PATTERN = r'm?(?P<month>1[0-2]|0[1-9])'
    DAY_OF_MONTH_PATTERN = r'(?P<day>3[0-1]|[1-2]\d|0[1-9])'
    DAY_OF_YEAR_PATTERN = (r'(?P<day>36[0-6]|3[0-5]\d|[1-2]\d\d|0[1-9]\d|00[1-9])')

    YEAR_MATCHER = re.compile(f'^.*/{YEAR_PATTERN}(/.*)?$')
    MONTH_MATCHER = re.compile(f'^.*/{YEAR_PATTERN}/?{MONTH_PATTERN}(/.*)?$')
    DAY_OF_MONTH_MATCHER = re.compile(
        f'^.*/{YEAR_PATTERN}/?{MONTH_PATTERN}/?{DAY_OF_MONTH_PATTERN}(/.*)?$')
    DAY_OF_YEAR_MATCHER = re.compile(f'^.*/{YEAR_PATTERN}/{DAY_OF_YEAR_PATTERN}(/.*)?$')

    def __init__(self, **kwargs):
        """
        `url` is the URL of the data repository to explore.
        `time_range` is a 2-tuple of datetime.datetime objects defining the time range
        of the datasets returned by the crawler.
        `include` is a regular expression string used to filter the crawler's output.
        Only URLs matching it are returned.
        """
        self.root_url = urlparse(kwargs['url'])
        self.time_range = kwargs['time_range']
        include = kwargs.get('include')
        self.include = re.compile(include) if include else None
        self.username = kwargs['username']
        self.password = kwargs['password']
        self._to_process = None

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"url='{self.root_url.geturl()}', "
                f"include='{self.include.pattern}', "
                f"time_range={self.time_range}, "
                f"username='{self.username}', "
                f"password='******'"
                ")")

    def __eq__(self, other):
        return (
            self.root_url == other.root_url and
            self.time_range == other.time_range and
            self.include == other.include and
            self.username == other.username and
            self.password == other.password)

    def _http_get(self, url, request_parameters=None, max_tries=5, wait_time=5):
        if self.username is not None and self.password is not None:
           if request_parameters is None:
               request_parameters = {}
           request_parameters['auth'] = (self.username, self.password)
        return super()._http_get(url, request_parameters=request_parameters,
                                 max_tries=max_tries, wait_time=wait_time)

    @property
    def base_url(self):
        """Get the root URL without the path"""
        return f"{self.root_url.scheme}://{self.root_url.netloc}"

    # ------------- crawl ------------
    def set_initial_state(self):
        """
        The `_urls` attribute contains URLs to the resources which
        will be returned by the crawler.
        The `_to_process` attribute contains URLs to pages which
        need to be searched for resources.
        """
        self._to_process = [self.root_url.path.rstrip('/')]

    def crawl(self):
        self.set_initial_state()
        while self._to_process:
            for dataset_info in self._process_folder(self._to_process.pop()):
                yield dataset_info

    @classmethod
    def _folder_coverage(cls, folder_path, time_zone=timezone.utc):
        """
        Find out if the folder has date info in its path.
        The maximum resolution is one day.
        For now, it supports the following structures:
          - .../yyyy/...
          - .../yyyy/mm/...
          - .../yyyymm/...
          - .../yyyy/mm/dd/...
          - .../yyyymmdd/...
          - .../yyyy/ddd/... (day of year)
        It will need to be updated to support new structures.
        """
        folder_coverage_start = folder_coverage_stop = None

        match_day = cls.DAY_OF_MONTH_MATCHER.search(folder_path)
        if match_day:
            folder_coverage_start = datetime(
                int(match_day.group('year')),
                int(match_day.group('month')),
                int(match_day.group('day')),
                tzinfo=time_zone)
            folder_coverage_stop = folder_coverage_start + timedelta(days=1)
            return (folder_coverage_start, folder_coverage_stop)

        match_day_of_year = cls.DAY_OF_YEAR_MATCHER.search(folder_path)
        if match_day_of_year:
            offset = timedelta(int(match_day_of_year.group('day')) - 1)
            folder_coverage_start = datetime(
                int(match_day_of_year.group('year')), 1, 1,
                tzinfo=time_zone) + offset
            folder_coverage_stop = folder_coverage_start + timedelta(days=1)
            return (folder_coverage_start, folder_coverage_stop)

        match_month = cls.MONTH_MATCHER.search(folder_path)
        if match_month:
            last_day_of_month = calendar.monthrange(
                int(match_month.group('year')), int(match_month.group('month')))[1]
            folder_coverage_start = datetime(
                int(match_month.group('year')),
                int(match_month.group('month')),
                1,
                tzinfo=time_zone)
            folder_coverage_stop = datetime(
                int(match_month.group('year')),
                int(match_month.group('month')),
                last_day_of_month,
                tzinfo=time_zone) + timedelta(days=1)
            return (folder_coverage_start, folder_coverage_stop)

        match_year = cls.YEAR_MATCHER.search(folder_path)
        if match_year:
            folder_coverage_start = datetime(int(match_year.group('year')), 1, 1,
                                             tzinfo=time_zone)
            folder_coverage_stop = datetime(int(match_year.group('year')) + 1, 1, 1,
                                            tzinfo=time_zone)
            return (folder_coverage_start, folder_coverage_stop)

        return (folder_coverage_start, folder_coverage_stop)

    def _intersects_time_range(self, start_time=None, stop_time=None):
        """
        Return True if either of these conditions is met:
          - a time coverage was extracted from the folder's path or a timestamp from the dataset's
            name, and this time coverage intersects with the Crawler's time range
          - no time range was defined when instantiating the crawler
          - no time coverage was extracted from the folder's url or dataset's name
        """
        return ((not start_time or not self.time_range[1] or start_time <= self.time_range[1]) and
                (not stop_time or not self.time_range[0] or stop_time >= self.time_range[0]))

    def _list_folder_contents(self, folder_path):
        """Lists the contents of a folder. Should return absolute paths"""
        raise NotImplementedError()

    def _is_folder(self, path):
        """Returns True if path points to a folder"""
        raise NotImplementedError()

    def get_download_url(self, path):
        """Get the download URL from a path in the repository
        """
        return urljoin(self.base_url, path)

    def _make_dataset_info(self, path):
        """Create a DatasetInfo from a path"""
        download_url = self.get_download_url(path)
        if download_url is not None:
            return DatasetInfo(download_url, self.get_raw_attributes(download_url))

    def _add_folder_to_process(self, path):
        """Add a folder to the list of folder which will be explored later"""
        if self._intersects_time_range(*self._folder_coverage(path)):
            if path not in self._to_process:
                self.logger.debug("Adding '%s' to the list of pages to process.", path)
                self._to_process.append(path)

    def _process_folder(self, folder_path):
        """
        Get the contents of a folder and feed the _urls (based on includes) and _to_process
        attributes
        """
        self.logger.debug("Looking for resources in '%s'...", folder_path)
        for path in self._list_folder_contents(folder_path):
            # deselect paths which contains any of the excludes strings
            if ((self.EXCLUDE and self.EXCLUDE.search(path)) or
                    self.root_url.path.startswith(path.rstrip(f"{os.sep}/"))):
                continue
            if self._is_folder(path):
                self._add_folder_to_process(path)
            # select paths which are matched based on input config file
            if self.include and self.include.search(path):
                dataset_info = self._make_dataset_info(path)
                if dataset_info is not None:
                    yield dataset_info

    def get_raw_attributes(self, download_url):
        """Gets raw attributes in the cases where they need to be
        fetched. For example, the y can sometimes be fetched from
        a different URL.
        """
        return {}


class HTMLDirectoryCrawler(DirectoryCrawler):
    """Implementation of DirectoryCrawler for repositories exposed as HTML pages."""
    name = 'html_directory'
    logger = logging.getLogger(__name__ + '.HTMLDirectoryCrawler')

    FOLDERS_SUFFIXES = ('/',)

    # ------------- crawl ------------
    @staticmethod
    def _strip_folder_page(folder_path):
        """
        Remove the index page of a folder path.
        For example: /foo/bar/contents.html becomes /foo/bar.
        """
        return re.sub(r'/(\w+\.html)?$', r'', folder_path)

    def _is_folder(self, path):
        return path.endswith(self.FOLDERS_SUFFIXES)

    @classmethod
    def _get_links(cls, html):
        """Returns the list of links contained in an HTML page, passed as a string"""
        parser = LinkExtractor()
        cls.logger.debug("Parsing HTML data.")
        parser.feed(html)
        return parser.links

    @staticmethod
    def _prepend_parent_path(parent_path, paths):
        """
        Prepend the parent_path to each path contained in paths,
        except if the path already starts with the parent_path.
        """
        result = []
        if not parent_path.endswith('/'):
            parent_path += '/'
        for path in paths:
            if urlparse(path).scheme != '':
                continue
            if path.startswith(parent_path):
                result.append(path)
            else:
                result.append(urljoin(parent_path, path))
        return result

    def _list_folder_contents(self, folder_path):
        request_parameters = {}
        html = self._http_get(f"{self.base_url}{folder_path}", request_parameters).text
        stripped_folder_path = self._strip_folder_page(folder_path)
        return self._prepend_parent_path(stripped_folder_path, self._get_links(html))


class OpenDAPCrawler(HTMLDirectoryCrawler):
    """
    Crawler for harvesting the data of OpenDAP
    """
    name = 'opendap'
    logger = logging.getLogger(__name__ + '.OpenDAPCrawler')
    FOLDERS_SUFFIXES = ('/contents.html',)
    EXCLUDE = re.compile(r'\?')
    GLOBAL_ATTRIBUTES_NAME = 'NC_GLOBAL'
    NAMESPACE_REGEX = r'^\{(\S+)\}Dataset$'

    # --------- get metadata ---------
    def _get_xml_namespace(self, root):
        """Try to get the namespace for the XML tag in the document from the root tag"""
        try:
            namespace_prefix = re.match(self.NAMESPACE_REGEX, root.tag)[1]  # first matched group
        except TypeError:
            namespace_prefix = ''
            self.logger.warning('Could not find XML namespace while reading DDX metadata')
        return namespace_prefix

    def _extract_attributes(self, root):
        """
        Extracts the global or specific attributes of a dataset or specific ones from a DDX document

        "x_path_global" is pointing to the 'NC_GLOBAL' part of response of the DDX document to
        obtain general information.
        "x_path_specific" is used to extract the dataset parameter names from the DDX document.
        """
        self.logger.debug("Getting the dataset's global attributes.")
        namespaces = {'default': self._get_xml_namespace(root)}
        extracted_attributes = {}
        x_path_global = "./default:Attribute[@name='NC_GLOBAL']/default:Attribute"
        x_path_specific = "./*/default:Attribute[@name='standard_name']"
        # finding the global metadata
        for attribute in root.findall(x_path_global, namespaces):
            extracted_attributes[attribute.get('name')] = attribute.find(
                "./default:value", namespaces).text
        # finding the parameters of the dataset that are declared in
        # the online source (specific metadata)
        # The specific ones are stored in 'raw_dataset_parameters' part of
        # the returned dictionary("extracted_attributes")
        extracted_attributes['raw_dataset_parameters'] = set()
        for attribute in root.findall(x_path_specific, namespaces):
            extracted_attributes['raw_dataset_parameters'].add(
                attribute.find("./default:value", namespaces).text)
        return extracted_attributes

    @classmethod
    def get_ddx_url(cls, url):
        """
        Converts the downloadable link into the link for reading meta data. In all cases,
        this method results in a url that ends with '.ddx' which will be used in further steps
        of ingestion.
        """
        if url.endswith('.ddx'):
            return url
        elif url.endswith('.dods'):
            return url[:-4]+'ddx'
        else:
            return url + '.ddx'

    def get_raw_attributes(self, url, **kwargs):
        """Get normalized metadata from the DDX info of the dataset located at
        the provided URL
        """
        ddx_url = self.get_ddx_url(url)
        # Get the metadata from the dataset as an XML tree
        stream = io.BytesIO(self._http_get(ddx_url, request_parameters={'stream': True}).content)
        # Add the metadata to the DatasetInfo
        return self._extract_attributes(ET.parse(stream).getroot())


class ThreddsCrawler(OpenDAPCrawler):
    """
    Crawler for harvesting the data which are provided by Thredds
    """
    name = 'thredds'
    logger = logging.getLogger(__name__ + '.ThreddsCrawler')
    FOLDERS_SUFFIXES = ('/catalog.html',)
    FILES_SUFFIXES = ('.nc',)
    EXCLUDE = re.compile(r'/thredds/catalog.html$')
    url_matcher = re.compile(r'^(.*)/(fileServer)/(.*)$')

    # --------- get metadata ---------
    @classmethod
    def get_ddx_url(cls, url):
        url_match = cls.url_matcher.match(url)
        if url_match:
            return f"{url_match[1]}/dodsC/{url_match[3]}.ddx"
        else:
            raise ValueError(f"{url} is not a Thredds HTTPServer URL")

    def get_download_url(self, path):
        result = None
        links = self._get_links(self._http_get(urljoin(self.base_url, path)).text)
        for link in links:
            if "fileServer" in link and link.endswith(self.FILES_SUFFIXES):
                result = f"{self.base_url}{link}"
                break
        return result


class FTPCrawler(DirectoryCrawler):
    """
    Crawler which returns the search results of an FTP, given the URL and search
    terms
    """
    name = 'ftp'
    logger = logging.getLogger(__name__ + '.FTPCrawler')

    def __init__(self, **kwargs):
        if not kwargs['url'].startswith('ftp://'):
            raise ValueError("The root url must start with 'ftp://'")

        username = kwargs.pop('username', 'anonymous')
        password = kwargs.pop('password', 'anonymous')
        self.ftp = None

        super().__init__(username=username, password=password, **kwargs)

    # ------------- crawl ------------
    def set_initial_state(self):
        """
        The `_urls` attribute contains URLs to the resources which will be returned by the crawler.
        The `_to_process` attribute contains URLs to pages which need to be searched for resources.
        """
        self._to_process = [self.root_url.path or '/']
        self.connect()

    def connect(self):
        """Creates an FTP connection and logs in"""
        self.ftp = ftplib.FTP(self.root_url.netloc, user=self.username, passwd=self.password)
        try:
            self.ftp.login(self.username, self.password)
        except ftplib.error_perm as err_content:
            # these errors happen when we try to log in twice, so they can be ignored
            if not (err_content.args[0].startswith('503') or err_content.args[0].startswith('230')):
                raise

    class Decorators():
        """Decorators for the FTPCrawler"""
        @staticmethod
        def retry_on_timeout(tries=2):
            """Wrapper around the retry decorator which
            enables to pass the number of tries"""
            def decorator_retry(method):
                """Decorator which re-creates the FTP connection
                if a timeout error occurs"""
                @functools.wraps(method)
                def wrapper_reconnect(crawler_instance, *args, **kwargs):
                    """Try to execute the decorated method.
                    If a FTP 421 error or a ConnectionError
                    (a network issue) occurs, re-create the connection
                    """
                    countdown = tries
                    last_error = None
                    while countdown > 0:
                        try:
                            return method(crawler_instance, *args, **kwargs)
                        except (ftplib.error_temp, ConnectionError) as error:
                            last_error = error
                            if isinstance(error, ftplib.error_temp) and '421' not in error.args[0]:
                                raise
                            else:
                                crawler_instance.logger.info("Re-initializing the FTP connection")
                                crawler_instance.connect()
                            countdown -= 1
                    if last_error:
                        raise last_error
                return wrapper_reconnect
            return decorator_retry

    @Decorators.retry_on_timeout(tries=5)
    def _list_folder_contents(self, folder_path):
        return self.ftp.nlst(folder_path)

    @Decorators.retry_on_timeout(tries=5)
    def _is_folder(self, path):
        """Determine if path is a folder by trying to change the working directory to path."""
        try:
            self.ftp.cwd(path)
        except ftplib.error_perm:
            return False
        else:
            return True


class LocalDirectoryCrawler(DirectoryCrawler):
    """Crawl through the contents of a local folder"""
    name = 'local'
    logger = logging.getLogger(__name__ + '.LocalDirectoryCrawler')

    # ------------- crawl ------------
    def _list_folder_contents(self, folder_path):
        if self._is_folder(folder_path):
            return [os.path.join(folder_path, file_path) for file_path in os.listdir(folder_path)]
        else:
            # if the given path points to a file, just return it
            return [folder_path]

    def _is_folder(self, path):
        return os.path.isdir(path)


class NansatCrawler(LocalDirectoryCrawler):
    """Crawler for local files, using Nansat to get metadata"""
    name = 'nansat'
    logger = logging.getLogger(__name__ + '.NansatCrawler')

    # --------- get metadata ---------
    def get_raw_attributes(self, dataset_path, **kwargs):
        """Gets dataset attributes using nansat"""
        raw_attributes = {}
        n_points = int(kwargs.get('n_points', 10))
        nansat_options = kwargs.get('nansat_options', {})
        url_scheme = urlparse(dataset_path).scheme
        if 'ftp' in url_scheme:
            raise ValueError(
                f"Can't ingest '{dataset_path}': nansat can't open remote ftp files")

        # Open file with Nansat
        nansat_object = Nansat(nansat_filename(dataset_path),
                               log_level=self.logger.getEffectiveLevel(),
                               **nansat_options)

        # get metadata from Nansat and get objects from vocabularies
        raw_attributes = nansat_object.get_metadata()

        # Find spatial coverage
        if nansat_object.vrt.dataset.GetGCPs():
            nansat_object.reproject_gcps()
        raw_attributes['location_geometry'] = shapely.wkt.loads(
            nansat_object.get_border_wkt(n_points=n_points))

        return raw_attributes


class NetCDFCrawler(LocalDirectoryCrawler):
    """Crawler for local NetCDF files"""
    name = 'netcdf'
    argument_parser = arguments.ArgumentParser([
        *LocalDirectoryCrawler.argument_parser.arguments.values(),
        arguments.StringArgument('longitude_attribute', default='LONGITUDE'),
        arguments.StringArgument('latitude_attribute', default='LATITUDE'),
    ])

    logger = logging.getLogger(__name__ + '.NetCDFCrawler')

    def __init__(self, *args, **kwargs):
        self.longitude_attribute = kwargs.pop('longitude_attribute')
        self.latitude_attribute = kwargs.pop('latitude_attribute')
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"url='{self.root_url.geturl()}', "
                f"include='{self.include.pattern}', "
                f"longitude_attribute='{self.longitude_attribute}', "
                f"latitude_attribute='{self.latitude_attribute}', "
                f"time_range={self.time_range}, "
                f"username='{self.username}', "
                f"password='******'"
                ")")

    # --------- get metadata ---------
    def _get_geometry_wkt(self, dataset):
        longitudes = dataset.variables[self.longitude_attribute][:]
        latitudes = dataset.variables[self.latitude_attribute][:]

        lonlat_dependent_data = False
        for nc_variable_name, nc_variable_value in dataset.variables.items():
            if (nc_variable_name not in dataset.dimensions
                    and self.longitude_attribute in nc_variable_value.dimensions
                    and self.latitude_attribute in nc_variable_value.dimensions):
                lonlat_dependent_data = True
                break

        # If at least a variable is dependent on latitude and
        # longitude, the longitude and latitude arrays are combined to
        # find all the data points
        if lonlat_dependent_data:
            valid_lon = longitudes.compressed() if np.ma.isMaskedArray(longitudes) else longitudes
            valid_lat = latitudes.compressed() if np.ma.isMaskedArray(latitudes) else latitudes
            points = list(itertools.product(valid_lon, valid_lat))
        # If the longitude and latitude variables have the same shape,
        # we assume that they contain the coordinates for each data
        # point
        elif longitudes.shape == latitudes.shape:
            masks = []
            for l in (longitudes, latitudes):
                if np.ma.isMaskedArray(l):
                    masks.append(l.mask)
                else:
                    masks.append(np.full(l.shape, False))
            combined_mask = np.logical_or(*masks)
            points = np.array(np.nditer((longitudes[~combined_mask],
                                         latitudes[~combined_mask]),
                                        flags=['buffered']))
        else:
            raise ValueError("Could not determine the spatial coverage")
        geometry = MultiPoint(points).convex_hull
        return geometry.wkt

    def get_raw_attributes(self, dataset_path):
        """Get the raw metadata from the NetCDF file"""
        dataset = netCDF4.Dataset(dataset_path)
        raw_attributes = dataset.__dict__
        raw_attributes['raw_dataset_parameters'] = self._get_parameter_names(dataset)
        raw_attributes['location_geometry'] = self._get_geometry_wkt(dataset)
        return raw_attributes

    def _get_parameter_names(self, dataset):
        """Get the names of the dataset's variables"""
        return [
            variable.standard_name
            for variable in dataset.variables.values()
            if hasattr(variable, 'standard_name')
        ]
