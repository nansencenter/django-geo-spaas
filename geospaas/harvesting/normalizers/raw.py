"""Raw normalizers"""
import re
from datetime import datetime, timezone

from .base import MetadataNormalizer
from .utils import NC_H5_FILENAME_MATCHER, raises
from ..utils import parse_timedelta_str


class RawMetadataNormalizer(MetadataNormalizer):
    """No guess work, just create a Dataset with an entry_id and a URL
    and optionally add the raw metadata as a tag
    Offers the possibility to specify a regex which will be applied to
    the URL to find a time.
    """

    name = 'raw'

    def __init__(self, **kwargs):
        """`time_regex`, if specified, should be a regex containing the
        following named groups:
        'year', 'month', 'day',         <- required
        'hour', 'minute', 'second'      <- optional
        The pattern will be matched against the full URL.
        """
        super().__init__(**kwargs)
        self.save_raw_metadata = kwargs.get('save_raw_metadata', True)
        self.time_regex = kwargs.get('time_regex', None)
        self.time_offset = parse_timedelta_str(kwargs.get('time_offset', '1s'))

    def get_entry_id(self, dataset_info):
        filename_match = NC_H5_FILENAME_MATCHER.search(dataset_info.url)
        if filename_match:
            return filename_match.group(1)
        else:
            return None

    @raises((AttributeError, KeyError))
    def get_time_coverage_start(self, dataset_info):
        if self.time_regex is not None:
            groups = re.match(self.time_regex, dataset_info.url).groupdict()
            year = int(groups['year'])
            month = int(groups['month'])
            day = int(groups['day'])
            hour = int(groups.get('hour', 0))
            minute = int(groups.get('minute', 0))
            second = int(groups.get('second', 0))
            return datetime(
                year=year,month=month,day=day,
                hour=hour, minute=minute, second=second,
                tzinfo=timezone.utc)
        return None

    @raises((AttributeError, KeyError))
    def get_time_coverage_end(self, dataset_info):
        if self.time_regex is not None:
            return self.get_time_coverage_start(dataset_info) + self.time_offset
        return None

    def get_location_geometry(self, dataset_info):
        return None

    def get_tags(self, dataset_info):
        tags_kwargs = []
        if self.save_raw_metadata:
            tags_kwargs = [
                {'name': key, 'value': str(value)}
                for key, value in dataset_info.metadata.items()
            ]
        return tags_kwargs
