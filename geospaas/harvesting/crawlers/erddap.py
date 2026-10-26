"""Crawlers for ERDDAP APIs"""
import logging
import re

import requests
import shapely.geometry

import geospaas.harvesting.arguments as arguments
from .base import Crawler, DatasetInfo


class ERDDAPTableCrawler(Crawler):
    """Crawler for ERDDAP tabledap APIs"""
    name = 'tabledap'
    argument_parser = arguments.ArgumentParser([
        *Crawler.argument_parser.arguments.values(),
        arguments.StringArgument('url', required=True),
        arguments.SequenceArgument(
            'id_attrs', required=True, contents_type=arguments.StringArgument),
        arguments.StringArgument('entry_id_prefix', default=''),
        arguments.StringArgument('longitude_attr', default='longitude'),
        arguments.StringArgument('latitude_attr', default='latitude'),
        arguments.StringArgument('time_attr', default='time'),
        arguments.StringArgument('position_qc_attr', default=''),
        arguments.StringArgument('time_qc_attr', default=''),
        arguments.SequenceArgument(
            'valid_qc_codes', contents_type=arguments.StringArgument, default=None),
        arguments.ListArgument('search_terms', default=None),
        arguments.WKTArgument('location', default=None, ),
        arguments.SequenceArgument(
            'variables', default=None, contents_type=arguments.StringArgument),
    ])
    logger = logging.getLogger(__name__ + '.ERDDAPTableCrawler')

    def __init__(self, **kwargs):
        url = kwargs['url']
        if url.rstrip('/').endswith('.json'):
            self.url = url
        else:
            raise ValueError("The URL should end with .json")
        self.id_attrs = kwargs['id_attrs']
        self.entry_id_prefix = kwargs['entry_id_prefix']
        self.longitude_attr = kwargs['longitude_attr']
        self.latitude_attr = kwargs['latitude_attr']
        self.time_attr = kwargs['time_attr']
        self.position_qc_attr = kwargs['position_qc_attr']
        self.time_qc_attr = kwargs['time_qc_attr']
        self.valid_qc_codes = kwargs['valid_qc_codes']
        self.search_terms = kwargs['search_terms'] if kwargs['search_terms'] is not None else []
        self.search_terms.extend(self._make_spatial_condition(kwargs['location']))
        self.search_terms.extend(self._make_temporal_condition(kwargs['time_range']))
        self.variables = kwargs['variables'] if kwargs['variables'] else []

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"url='{self.url}', "
                f"id_attrs={self.id_attrs}, "
                f"entry_id_prefix='{self.entry_id_prefix}', "
                f"longitude_attr='{self.longitude_attr}', "
                f"latitude_attr='{self.latitude_attr}', "
                f"time_attr='{self.time_attr}', "
                f"position_qc_attr='{self.position_qc_attr}', "
                f"time_qc_attr='{self.time_qc_attr}', "
                f"valid_qc_codes={self.valid_qc_codes}, "
                f"search_terms={self.search_terms}, "
                f"variables={self.variables}"
                ")")

    def __eq__(self, other):
        return (
            self.url == other.url and
            self.id_attrs == other.id_attrs and
            self.longitude_attr == other.longitude_attr and
            self.latitude_attr == other.latitude_attr and
            self.time_attr == other.time_attr and
            self.position_qc_attr == other.position_qc_attr and
            self.time_qc_attr == other.time_qc_attr and
            self.valid_qc_codes == other.valid_qc_codes and
            self.search_terms == other.search_terms and
            self.variables == other.variables
        )

    def get_ids(self):
        """Fetch identifiers matching the search terms"""
        url = f"{self.url}?{','.join(self.id_attrs)}&distinct()"
        kwargs = {}
        url = '&'.join([url] + self.search_terms)
        try:
            response = self._http_get(url, max_tries=1, **kwargs)
        except requests.HTTPError as error:
            self.logger.error("Could not list dataset identifiers at %s: %s",
                              url, error.response.content, exc_info=True)
            raise
        for row in response.json()['table']['rows']:
            yield row[:len(self.id_attrs)]

    def _make_condition_parameters(self, parameters):
        """Prepare the parameters to filter a query using the id
        attributes. Necessary because the API requires different
        formats depending on the type of parameter
        """
        params = {}
        for key, value in parameters.items():
            if isinstance(value, str):
                params[key] = f'"{value}"'
            else:
                params[key] = value
        return params

    def _make_spatial_condition(self, location):
        """Make a tabledap spatial condition from a shapely geometry"""
        result = []
        if location:
            min_lon, min_lat, max_lon, max_lat = location.bounds
            result = [
                f"{self.longitude_attr}>={min_lon}",
                f"{self.longitude_attr}<={max_lon}",
                f"{self.latitude_attr}>={min_lat}",
                f"{self.latitude_attr}<={max_lat}",
            ]
        return result

    def _make_temporal_condition(self, time_range):
        """Make a tabledap spatial condition from a couple of datetime
        objects
        """
        result = []
        time_format = '%Y-%m-%dT%H:%M:%SZ'
        if time_range[0]:
            result.append(f"{self.time_attr}>={time_range[0].strftime(time_format)}")
        if time_range[1]:
            result.append(f"{self.time_attr}<={time_range[1].strftime(time_format)}")
        return result

    def crawl(self):
        attributes = [self.time_attr, self.longitude_attr, self.latitude_attr]
        for qc_attr in (self.time_qc_attr, self.position_qc_attr):
            if qc_attr:
                attributes.append(qc_attr)
        attributes.extend(self.variables)
        for id_values in self.get_ids():
            id_attrs = dict(zip(self.id_attrs, id_values))
            id_condition = '&'.join(
                f"{id_attr}={id_value}"
                for id_attr, id_value in self._make_condition_parameters(id_attrs).items()
            )
            coverage = self.get_coverage(id_attrs)
            yield DatasetInfo(
                f'{self.url}?{",".join(attributes)}&{id_condition}',
                {
                    'entry_id': self._make_entry_id(id_values),
                    'temporal_coverage': coverage[0],
                    'trajectory': shapely.geometry.MultiPoint(coverage[1]).wkt,
                    'product_metadata': self.get_product_metadata(),
                })

    def _make_entry_id(self, id_values):
        """Create an entry_id from the prefix and values of the
        identifying attributes
        """
        return self.entry_id_prefix + '_'.join(map(str, id_values))

    def _check_qc(self, qc_value):
        """Return True if the QC value indicates valid data or the
        valid codes are unknown
        """
        return not self.valid_qc_codes or qc_value in self.valid_qc_codes

    def _make_coverage_url(self):
        """"""
        qc_attributes = ','.join(c for c in (self.time_qc_attr, self.position_qc_attr) if c)
        if qc_attributes:
            qc_attributes = f",{qc_attributes}"
        return (f'{self.url}?{self.time_attr},{self.longitude_attr},{self.latitude_attr}' +
                qc_attributes +
                f'&distinct()&orderBy("{self.time_attr}")')

    def get_coverage(self, id_attributes):
        """Get the temporal and spatial coverage for a specific dataset
        """
        try:
            response = self._http_get(self._make_coverage_url(), request_parameters={
                'params': self._make_condition_parameters(id_attributes)
            })
        except requests.HTTPError as error:
            self.logger.error("Could not get coverage for dataset %s: %s",
                              id_attributes, error.response.content)
            raise
        rows = response.json()['table']['rows']

        # build the trajectory and get the first time with valid QC
        # (the query results are sorted by time)
        time_coverage_start = None
        trajectory = []
        for row in rows:
            if time_coverage_start is None and self._check_qc(row[3]):
                time_coverage_start = row[0]
            point = (row[1], row[2])
            if point not in trajectory and self._check_qc(row[4]):
                trajectory.append(point)

        # get the last time with valid QC
        time_coverage_end = None
        for row in rows[::-1]:
            if self._check_qc(row[3]):
                time_coverage_end = row[0]
                break

        if time_coverage_start is None or time_coverage_end is None or not trajectory:
            raise RuntimeError(f"Could not determine coverage for dataset {id_attributes}")

        return ((time_coverage_start, time_coverage_end), trajectory)

    def _make_product_metadata_url(self):
        """Generate the product metadata URL from the base data URL"""
        match = re.match(r'^(https?://.*)/tabledap/(.*)\.json$', self.url)
        if match:
            return f"{match.group(1)}/info/{match.group(2)}/index.json"
        else:
            raise RuntimeError(f"Unable to get product metadata URL from {self.url}")

    def get_product_metadata(self):
        """Get the product's metadata"""
        url = self._make_product_metadata_url()
        try:
            response = self._http_get(url)
        except requests.HTTPError:
            self.logger.info("Could not get product metadata from %s", url)
            raise
        return response.json()
