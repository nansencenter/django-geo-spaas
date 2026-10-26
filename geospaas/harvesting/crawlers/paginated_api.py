"""Crawlers for paginated APIs"""
import json
import logging
import math

from shapely.geometry import LineString, Point, Polygon

import geospaas.harvesting.arguments as arguments
import geospaas.harvesting.utils as utils
from .base import Crawler, DatasetInfo


class HTTPPaginatedAPICrawler(Crawler):
    """Base class for crawlers used on repositories exposing a paginated API over HTTP"""
    name = None
    argument_parser = arguments.ArgumentParser([
        *Crawler.argument_parser.arguments.values(),
        arguments.StringArgument('url', required=True),
        arguments.DictArgument('search_terms', default=None),
        arguments.IntegerArgument('page_size', default=100),
        arguments.IntegerArgument('initial_offset', default=None),
        arguments.WKTArgument('location', default=None),
    ])

    PAGE_OFFSET_NAME = ''
    PAGE_SIZE_NAME = ''
    MIN_OFFSET = 0

    def __init__(self, **kwargs):
        self.root_url = kwargs['url'].rstrip('/')
        self.initial_offset = kwargs['initial_offset'] or self.MIN_OFFSET
        self.request_parameters = self._build_request_parameters(
            kwargs['search_terms'], kwargs['time_range'], kwargs['location'],
            kwargs['username'], kwargs['password'],
            kwargs['page_size'])

    @property
    def url(self):
        return self.root_url

    def __eq__(self, other):
        return (
            self.url == other.url and
            self.initial_offset == other.initial_offset and
            self.request_parameters == other.request_parameters
        )

    def __repr__(self):
        request_parameters = self.request_parameters.copy()
        request_parameters['params'] = utils.mask_secrets(request_parameters['params'])
        return (f"{self.__class__.__name__}("
                f"url='{self.url}', "
                f"initial_offset={self.initial_offset}, "
                f"request_parameters={request_parameters}"
                ")")

    # ------------- crawl ------------
    @property
    def page_size(self):
        """Getter for the page size"""
        return self.request_parameters['params'][self.PAGE_SIZE_NAME]

    @property
    def page_offset(self):
        """Getter for the page offset"""
        return self.request_parameters['params'][self.PAGE_OFFSET_NAME]

    @page_offset.setter
    def page_offset(self, offset):
        """Setter for the page offset"""
        self.request_parameters['params'][self.PAGE_OFFSET_NAME] = offset

    def increment_offset(self):
        self.page_offset += 1

    def _build_request_parameters(self, search_terms=None, time_range=(None, None), location=None,
                                  username=None, password=None, page_size=100):
        """Build a dict containing the parameters used to query the API.
        This dict will be unpacked to provide the arguments to `requests.get()`.
        """
        return {
            'params': {
                self.PAGE_OFFSET_NAME: self.initial_offset,
                self.PAGE_SIZE_NAME: page_size,
            }
        }

    def set_initial_state(self):
        self.page_offset = self.initial_offset

    def crawl(self):
        self.set_initial_state()
        while True:
            entries = self._get_entries(self._get_next_page())
            if not entries:
                break
            for dataset_info in self._get_datasets_info(entries):
                yield dataset_info

    def _get_next_page(self):
        """Get the next page of search results"""
        self.logger.debug("Looking for resources at '%s', matching '%s'",
                         self.url, self.request_parameters['params'])
        current_page = self._http_get(self.url, self.request_parameters).text
        self.increment_offset()
        return current_page

    def _get_entries(self, page):
        """Get entries about datasets from the pages returned by the
        API
        """
        raise NotImplementedError()

    def _get_datasets_info(self, entries):
        """Get datasets information from raw entries and yield
        DatasetInfo objects.
        """
        raise NotImplementedError()


class EarthDataCMRCrawler(HTTPPaginatedAPICrawler):
    """Crawler for the CMR Earthdata search API"""
    name = 'earthdata_cmr'
    argument_parser = arguments.ArgumentParser([
        *HTTPPaginatedAPICrawler.argument_parser.arguments.values(),
        arguments.WKTOrStringArgument(
            'location', geometry_types=[Polygon, LineString, Point], default=None),
        arguments.ArgumentParser(name='search_terms', arguments=[
            arguments.StringArgument('bounding_box', required=False),
            arguments.StringArgument(
                'short_name', required=True, description='Short name of the collection'),
            arguments.ChoiceArgument(
                'downloadable', valid_options=['true', 'false'], default='true'),
            arguments.StringArgument('platform'),
            arguments.StringArgument('instrument'),
            arguments.StringArgument('sensor'),
        ]),
    ])
    PAGE_OFFSET_NAME = 'page_num'
    PAGE_SIZE_NAME = 'page_size'
    MIN_OFFSET = 1

    # ------------- crawl ------------
    def _build_request_parameters(self, search_terms=None, time_range=(None, None), location=None,
                                  username=None, password=None, page_size=100):
        if location is not None:
            search_terms.update(self._make_spatial_parameter(location))

        request_parameters = super()._build_request_parameters(
            search_terms, time_range, location, username, password, page_size)

        if search_terms:
            request_parameters['params'].update(**search_terms)

        # sort by start date, ascending
        request_parameters['params']['sort_key'] = '+start_date'

        if time_range[0] or time_range[1]:
            request_parameters['params']['temporal'] = ','.join(
                date.isoformat() if date else ''
                for date in time_range)

        return request_parameters

    def _exclude_edges(self, raw_points):
        """Slightly move points on the edges inward for compatibility with the
        Earthdata CMR interface
        """
        points = []
        for lon, lat in raw_points:
            abs_lon = abs(lon)
            abs_lat = abs(lat)
            if abs_lon == 180:
                lon = math.copysign(abs_lon - .01, lon)
            if abs_lat == 90:
                lat = math.copysign(abs_lat - .01, lat)
            points.append((lon, lat))
        return points

    def _make_spatial_parameter(self, geometry):
        if isinstance(geometry, Polygon):
            # the API takes a sequence of points to define a polygon:
            # lon0,lat0,lon1,lat1,lon2,lat2,...,lon0,lat0
            points= self._exclude_edges(zip(*geometry.exterior.coords.xy))
            result = {'polygon[]': ','.join([f"{lon},{lat}" for lon, lat in points])}
        elif isinstance(geometry, LineString):
            points = self._exclude_edges(zip(*geometry.xy))
            result = {'line[]': ','.join([f"{lon},{lat}" for lon, lat in points])}
        elif isinstance(geometry, Point):
            result = {'point': f"{geometry.xy[0][0]},{geometry.xy[1][0]}"}
        elif isinstance(geometry, str):
            name, value = geometry.split('=')
            result = {name: value}
        else:
            raise ValueError(f"Unsupported geometry type {type(geometry)}")
        return result

    def _find_download_url(self, entry):
        """Return the first URL whose type is 'GET DATA'"""
        urls = entry['umm']['RelatedUrls']
        for url in urls:
            if url.get('Type', '').lower() == 'get data':
                return url['URL']
        return urls[0]['URL']

    def _get_entries(self, page):
        return json.loads(page)['items']

    def _get_datasets_info(self, entries):
        """Get dataset attributes from the current page and
        yields them"""
        for entry in entries:
            url = self._find_download_url(entry)
            yield DatasetInfo(url, entry)


class RestoCrawler(HTTPPaginatedAPICrawler):
    """Crawler for the Creodias EO finder API"""
    name = 'resto'
    argument_parser = arguments.ArgumentParser([
        *HTTPPaginatedAPICrawler.argument_parser.arguments.values(),
        arguments.StringArgument('collection', required=True),
        arguments.ArgumentParser(name='search_terms', strict=False, arguments=[
            arguments.StringArgument('status', default='all'),
            arguments.StringArgument('dataset', default='ESA-DATASET'),
            arguments.StringArgument('productIdentifier', required=False),
            arguments.StringArgument('productType', required=False),
            arguments.StringArgument('processingLevel', required=False),
            arguments.StringArgument('platform', required=False),
            arguments.StringArgument('instrument', required=False),
            arguments.StringArgument('resolution', required=False),
            arguments.StringArgument('organisationName', required=False),
            arguments.StringArgument('orbitNumber', required=False),
            arguments.StringArgument('sensorMode', required=False),
            arguments.StringArgument('cloudCover', required=False),
            arguments.StringArgument('updated', required=False),
            arguments.StringArgument('publishedAfter', required=False),
            arguments.StringArgument('publishedBefore', required=False),
            arguments.StringArgument('exactCount', required=False),
            arguments.StringArgument('phase', required=False),
            arguments.StringArgument('cycle', required=False),
            arguments.StringArgument('bands', required=False),
            arguments.StringArgument('path', required=False),
            arguments.StringArgument('row', required=False),
            arguments.StringArgument('sunAzimuth', required=False),
            arguments.StringArgument('sunElevation', required=False),
            arguments.StringArgument('version', required=False),
            arguments.StringArgument('orbitDirection', required=False),
            arguments.StringArgument('timeliness', required=False),
            arguments.StringArgument('relativeOrbitNumber', required=False),
            arguments.StringArgument('processingBaseline', required=False),
            arguments.StringArgument('polarisation', required=False),
            arguments.StringArgument('swath', required=False),
            arguments.StringArgument('tileId', required=False),
        ]),
    ])
    logger = logging.getLogger(__name__ + '.RestoCrawler')

    PAGE_OFFSET_NAME = 'page'
    PAGE_SIZE_NAME = 'maxRecords'
    MIN_OFFSET = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.root_url = f"{self.url}/resto/api/collections/{kwargs['collection']}/search.json"

    # ------------- crawl ------------
    def _build_request_parameters(self, search_terms=None, time_range=(None, None), location=None,
                                  username=None, password=None, page_size=100):
        """Build a dict containing the parameters used to query
        the Creodias EO finder API.
        search_terms should be a dictionary containing the search
        parameters and their values.
        Results are sorted ascending, which avoids missing some
        if products are added while the harvesting is happening
        (it will generally be the case)
        """
        request_parameters = super()._build_request_parameters(
            search_terms, time_range, location, username, password, page_size)

        if search_terms is not None:
            if location is not None:
                search_terms['geometry'] = location.wkt
            request_parameters['params'].update(**search_terms)

        request_parameters['params']['sortParam'] = 'published'
        request_parameters['params']['sortOrder'] = 'ascending'

        api_date_format = '%Y-%m-%dT%H:%M:%SZ'
        if time_range[0]:
            request_parameters['params']['startDate'] = time_range[0].strftime(api_date_format)
        if time_range[1]:
            request_parameters['params']['completionDate'] = time_range[1].strftime(api_date_format)

        return request_parameters

    def _get_entries(self, page):
        return json.loads(page)['features']

    def _get_datasets_info(self, entries):
        """Get dataset attributes from the current page and
        yields them.
        Returns True if attributes were found, False otherwise"""
        for entry in entries:
            metadata = entry['properties']
            metadata['geometry'] = json.dumps(entry['geometry'])
            url = metadata['services']['download']['url']
            yield DatasetInfo(url, metadata)


class ODataCrawler(HTTPPaginatedAPICrawler):
    """Crawler for the Copernicus OData API"""
    name = 'odata'
    argument_parser = arguments.ArgumentParser([
        *HTTPPaginatedAPICrawler.argument_parser.arguments.values(),
        arguments.StringArgument('collection', required=True),
        arguments.StringArgument('download_url', required=False),
    ])
    logger = logging.getLogger(__name__ + '.ODataCrawler')

    PAGE_OFFSET_NAME = '$skip'
    PAGE_SIZE_NAME = '$top'
    MIN_OFFSET = 0

    def __init__(self, **kwargs):
        self.root_url = kwargs['url'].rstrip('/')
        self.download_url_base = kwargs.get('download_url')
        self.collection = kwargs['collection']
        self._collection_attributes = None
        super().__init__(**kwargs)

    @property
    def url(self):
        return f"{self.root_url}/Products"

    def increment_offset(self):
        self.page_offset += self.page_size

    @property
    def collection_attributes(self):
        """Fetches valid attributes depending on the collection"""
        if self._collection_attributes is None:
            attributes_list = self._http_get(
                f"{self.root_url}/Attributes({self.collection})"
            ).json()
            self._collection_attributes = {
                attribute['Name']: attribute['ValueType']
                for attribute in attributes_list
            }
        return self._collection_attributes

    # ------------- crawl ------------
    def _build_request_parameters(self, search_terms=None, time_range=(None, None), location=None,
                                  username=None, password=None, page_size=100):
        request_parameters = super()._build_request_parameters(
            search_terms, time_range, location, username, password, page_size)
        request_parameters['params']['$orderby'] = 'ContentDate/Start asc'
        request_parameters['params']['$expand'] = 'Attributes'

        collection_filter = [f"Collection/Name eq '{self.collection}'"]

        search_terms_filter = self._build_attributes_filters(search_terms) if search_terms else []

        api_date_format = '%Y-%m-%dT%H:%M:%SZ'
        time_filter = []
        if time_range[0]:
            time_filter.append(f"ContentDate/End gt {time_range[0].strftime(api_date_format)}")
        if time_range[1]:
            time_filter.append(f"ContentDate/Start lt {time_range[1].strftime(api_date_format)}")

        spatial_filter = []
        if location:
            spatial_filter.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{location}')")

        request_parameters['params']['$filter'] = ' and '.join(
            collection_filter + search_terms_filter + time_filter + spatial_filter)

        return request_parameters

    def _build_attributes_filters(self, attributes: dict):
        """Build a list of filters based on attributes.
        For now, the only test supported is if the attribute is equal
        to the provided value
        """
        filters = []
        for name, value in attributes.items():
            try:
                attribute_type = self.collection_attributes[name]
            except KeyError:
                self.logger.warning("%s is not a valid attribute for collection %s",
                                    name, self.collection)
                continue
            filters.append(
                f"Attributes/OData.CSC.{attribute_type}Attribute/any("
                    f"att:att/Name eq '{name}' and "
                    f"att/OData.CSC.{attribute_type}Attribute/Value eq '{value}')")
        return filters

    def _get_entries(self, page):
        return json.loads(page)['value']

    def get_download_url(self, dataset_id):
        if self.download_url_base:
            base_url = f"{self.download_url_base.rstrip('/')}/Products"
        else:
            base_url = self.url
        return f"{base_url}({dataset_id})/$value"

    def _get_datasets_info(self, entries):
        """Get dataset attributes from the current page and
        yields them.
        Returns True if attributes were found, False otherwise"""
        for entry in entries:
            metadata = entry
            url = self.get_download_url(entry['Id'])
            yield DatasetInfo(url, metadata)
