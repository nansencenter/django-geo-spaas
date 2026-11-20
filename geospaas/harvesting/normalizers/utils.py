"""Utility functions for metadata normalizing"""

import functools
import re
from datetime import datetime, timedelta

import shapely.geometry
import shapely.ops
import shapely.wkt
from dateutil.tz import tzutc
from django.db.models import Case, When

from geospaas.vocabularies.models import Keyword, Parameter

from .errors import MetadataNormalizationError


######################## Pythesint utilities ########################

# Field names commonly used in the 'summary' attribute
SUMMARY_FIELDS = {
    'description': 'Description',
    'processing_level': 'Processing level',
    'product': 'Product',
}


# Key: valid pythesint search keyword
# Value: iterable of aliases
PYTHESINT_KEYWORD_TRANSLATION = {
    # instruments
    'OLCI': ('OL',),
    'SLSTR': ('SL',),
    # platforms
    'METEOSAT-10': ('MSG3',),
    'METEOSAT-11': ('MSG4',),
    'METEOSAT-8': ('MSG1',),
    'METEOSAT-9': ('MSG2',),
    'METOP-B': ('METOP_B',),
    'Sentinel-1A': ('S1A',),
    'Sentinel-1B': ('S1B',),
    'Sentinel-2A': ('S2A',),
    'Sentinel-2B': ('S2B',),
    'Sentinel-3A': ('S3A',),
    'Sentinel-3B': ('S3B',),
    'argo-float': ('Argo float',),
    # providers
    'ESA/EO': ('ESA',),
    'OB.DAAC': ('OB_DAAC',),
    'NASA/JPL/PODAAC': ('POCLOUD',),
    'C-SAR': ('SAR-C', 'SAR-C SAR'),
    'EUMETSAT/OSISAF': ('EUMETSAT OSI SAF',),
    'NSIDC': ('NSIDC_ECS',),
}

def translate_pythesint_keyword(translation_dict, alias):
    """Get a valid pythesint search keyword from known aliases"""
    for valid_keyword, aliases in translation_dict.items():
        if alias in aliases:
            return valid_keyword
    return alias


######################## Time utilities ########################

YEARMONTH_REGEX = r'(?P<year>\d{4})(?P<month>\d{2})'
YEARMONTHDAY_REGEX = YEARMONTH_REGEX + r'(?P<day>\d{2})'

def create_datetime(year, month=1, day=1, day_of_year=None, hour=0, minute=0, second=0):
    """Returns a datetime object using the provided arguments.
    Possible argument combinations are:
      - year, month, day(, hour, minute, second)
      - year, day_of_year(, hour, minute, second)
    """
    year = int(year)
    hour = int(hour)
    minute = int(minute)
    second = int(second)

    if day_of_year:
        day_of_year = int(day_of_year)
        first_day = datetime(year, 1, 1, hour, minute, second).replace(tzinfo=tzutc())
        return first_day + timedelta(days=day_of_year-1)
    else:
        month = int(month)
        day = int(day)
        return datetime(year, month, day, hour, minute, second).replace(tzinfo=tzutc())

def find_time_coverage(time_patterns, url):
    """Find the time coverage based on the 'url' raw attribute.
    Returns a 2-tuple containing the start and end time,
    or a 2-tuple containing None if no time coverage was found.

    This method uses the `time_patterns` dictionary.
    This dictionary has the following structure:
    time_patterns = [
        (
            compiled_regex,
            datetime_creation_function,
            time_coverage_function
        ),
        (...)
    ]
    Where:
        - "url_prefix" is the prefix matched against the 'url' raw
        attribute

        - "compiled_regex" is a compiled regular expresion used to
        extract the time information from the URL. It should
        contain named groups which will be given as arguments
        to the datetime_creation_function

        - "datetime_creation_function" is a function which creates
        a datetime object from the information extracted using
        the regex.

        - "time_coverage_function" is a function which takes the
        datetime object returned by datetime_creation_function
        and returns the time coverage as a 2-tuple
    """
    for matcher, get_time, get_coverage in time_patterns:
        match = matcher.search(url)
        if match:
            file_time = get_time(**match.groupdict())
            return (get_coverage(file_time)[0], get_coverage(file_time)[1])
    raise MetadataNormalizationError(f"Could not extract the time coverage from {url}")

######################## Spatial utilities ########################


def wkt_polygon_from_wgs84_limits(north, south, east, west):
    """
    Returns a WKT string representation of a simple boundary box delimited by its northernmost
    latitude, southernmost latitude, easternmost longitude and westernmost longitude
    """
    return f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"


def translate_west_coordinates(multipolygon):
    """Translate west coordinates from [-180, 0[ to [180, 360[
    Should be used on a shapely multipolygon
    """

    def translate_point(point):
        return (point[0] + 360, point[1]) if point[0] < 0 else point

    def translate_ring(ring):
        return shapely.geometry.LinearRing(translate_point(point) for point in ring.coords)

    new_polygons = []
    for polygon in multipolygon.geoms:

        exterior_ring = translate_ring(polygon.exterior)

        new_interior_rings = []
        for ring in polygon.interiors:
            new_interior_rings.append(translate_ring(ring))

        new_polygons.append(shapely.geometry.Polygon(exterior_ring, new_interior_rings))

    return shapely.geometry.MultiPolygon(new_polygons)


def restore_west_coordinates(multipolygon):
    """Translate west coordinates back from [180, 360[ to [-180, 0[
    Should be used on a shapely multipolygon split along the IDL
    """

    def restore_point(point, is_east):
        """Restores a point's longitude to the [-180, 0[ range. If the
        current polygon is on the west side of the IDL, points located
        on the IDL which have a longitude of 180 are translated to
        -180.
        """
        if point[0] > 180 or (point[0] == 180 and not is_east):
            lon = point[0] - 360
        else:
            lon = point[0]
        return (lon, point[1])

    def restore_ring(ring):
        return shapely.geometry.LinearRing(restore_point(point, is_east) for point in ring.coords)

    new_polygons = []
    for polygon in multipolygon.geoms:
        # Determine if this polygon is on the east or west side of the
        # IDL. It has been split already, so it is either east or west.
        # We find the first point which is not on the IDL and check
        # whether it is east or west.
        for point in polygon.exterior.coords:
            if point[0] == 180:
                continue
            else:
                # we deal with translated coordinates, so west
                # coordinates are in [180, 360[
                is_east = point[0] < 180
                break

        exterior_ring = restore_ring(polygon.exterior)
        interior_rings = []
        for ring in polygon.interiors:
            interior_rings.append(restore_ring(ring))
        new_polygons.append(shapely.geometry.Polygon(exterior_ring, interior_rings))

    return shapely.geometry.MultiPolygon(new_polygons)


def split_multipolygon_along_idl(multipolygon):
    """Split multipolygons which cross the international dateline to
    avoid undesired side effects
    """
    # if the multipolygon has global coverage, return it as is
    if shapely.wkt.loads(WORLD_WIDE_COVERAGE_WKT).difference(multipolygon).is_empty:
        return multipolygon

    # translate the longitude of west points from  the range [-180, 0[
    # to [180, 360[. This makes it easy to split the multipolygon along
    # the IDL
    translated_geometry = translate_west_coordinates(multipolygon)

    # split the multipolygon along the IDL
    line = shapely.geometry.LineString(((180, 90), (180, -90)))
    split_geometry = shapely.ops.split(translated_geometry, line)

    # restore the longitude of west points to [-180, 0[ and return
    # the result
    return restore_west_coordinates(split_geometry)


######################## Other utilities ########################

UNKNOWN = 'Unknown'
NC_H5_FILENAME_MATCHER = re.compile(r"([^/]+)\.(nc|h5)(\.gz)?$")
WORLD_WIDE_COVERAGE_WKT = 'POLYGON((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'


def dict_to_string(dictionary):
    """Returns a string representation of the dictionary argument.
    The following dictionary:
    {'key1': 'value1', 'key2': 'value2'}
    Will be represented as:
    "key1: value1;key2: value2"
    """
    string = ''
    for key, value in dictionary.items():
        string += f"{key}: {value};"
    return string.rstrip(';')


def raises(exceptions):
    """Decorator for methods which get an attribute from metadata.
    Makes it possible to declare which exception(s) are thrown when the
    raw metadata does not have the expected structure.
    `exceptions` can be an exception class or a tuple of exception
    classes. If any of these exceptions is raised by the method,
    a MetadataNormalizationError with a (hopefully) clear error message
    is raised from this exception.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, dataset_info):
            try:
                return func(self, dataset_info)
            except exceptions as error:
                raise MetadataNormalizationError(
                    f"{func.__name__} was unable to process the following metadata: {dataset_info.metadata}"
                ) from error
        return wrapper
    return decorator


def create_parameter_list(parameters):
    """Tries to find Parameter objects which match the given names
    """
    normalized_dataset_parameters = []
    for parameter_name in parameters:
        candidates = Parameter.objects.filter(data__standard_name=parameter_name)
        if not candidates.exists():
            continue
        else:
            if candidates.count() > 1:
                # if several options are available, prioriy
                # goes to the one from the CF standard with the
                # highest version
                voc_priorities = ('cf_standard_name', 'wkv_variable')
                for vocabulary in voc_priorities:
                    voc_candidates = candidates.filter(kind=vocabulary)
                    if voc_candidates.exists():
                        candidates = voc_candidates.order_by('-version')
                        break
            normalized_dataset_parameters.append(candidates.first())
    return normalized_dataset_parameters


def find_keywords(lookups):
    """Look for keywords matching criteria.
    `search_terms` is a list of Django lookups in the form of
    dictionaries
    """
    keywords = []
    for lookup in lookups:
        candidates = Keyword.objects.filter(**lookup).order_by(
            Case(When(kind='legacy', then=1), default=2)) # legacy keywords have the lowest priority
        if candidates.exists() and candidates.first() not in keywords:
            keywords.append(candidates.first())
    return keywords
