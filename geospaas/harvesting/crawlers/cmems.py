"""CMEMS crawlers"""
import calendar
import tempfile

import copernicusmarine

import geospaas.harvesting.arguments as arguments
from .base import Crawler, DatasetInfo


class CMEMSCrawler(Crawler):
    """Crawler which accesses CMEMS products through the
    copernicusmarine toolbox
    """
    name = 'cmems'
    argument_parser = arguments.ArgumentParser([
        *Crawler.argument_parser.arguments.values(),
        arguments.StringArgument('product_id', required=True),
        arguments.SequenceArgument('dataset_ids',
                                   contents_type=arguments.StringArgument, required=True),
    ])

    def __init__(self, **kwargs):
        self.product_id = kwargs['product_id']
        self.dataset_ids = kwargs['dataset_ids']
        self.time_range = kwargs['time_range']
        self.username = kwargs['username']
        self.password = kwargs['password']
        # initialized in self.set_initial_state()
        self._product_info = None
        self._normalizer = None

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"product_id={self.product_id}, "
                f"dataset_ids={self.dataset_ids}, "
                f"time_range={self.time_range}, "
                f"username={self.username}, "
                f"password=******"
                ")")

    def __eq__(self, other):
        return (
            self.product_id == other.product_id and
            self.dataset_ids == other.dataset_ids and
            self.time_range == other.time_range and
            self.username == other.username and
            self.password == other.password)

    def make_filter(self):
        """Create a regular expression based on a time range.
        Granularity: 1 day
        """
        first_date = self.time_range[0]
        last_date = self.time_range[1]

        if first_date is None or last_date is None:
            return None

        years = list(range(first_date.year, last_date.year + 1))
        years_regex = []
        for year in years:
            # small optimisation to match whole years without going
            # down to the day-by-day level
            if year > first_date.year and year < last_date.year:
                years_regex.append(f"({year}[0-9]{{4}})")
                continue

            if year == first_date.year:
                first_month = first_date.month
            else:
                first_month = 1

            if year == last_date.year:
                last_month = last_date.month
            else:
                last_month = 12

            months_regex = []
            for month in list(range(first_month, last_month + 1)):
                # small optimisation to match whole months without going
                # down to the day-by-day level
                if (first_date.year != last_date.year and
                        ((year == first_date.year and month > first_date.month)
                         or (year == last_date.year and month < last_date.month))):
                    years_regex.append(f"({year}{month:02d}[0-3][0-9])")
                    continue

                if year == first_date.year and month == first_month:
                    first_day = first_date.day
                else:
                    first_day = 1

                if year == last_date.year and month == last_month:
                    last_day = last_date.day
                else:
                    last_day = calendar.monthrange(year, month)[1]

                days_regex = '|'.join((f"{day:02d}" for day in range(first_day, last_day + 1)))
                months_regex.append(f"{month:02d}({days_regex})")

            years_regex.append(f"({year}({'|'.join(months_regex)}))")
            full_regex = '|'.join(years_regex)

        return f"^(.*_({full_regex})_.*)|({full_regex}.*)$"

    def set_initial_state(self):
        """Download lists of dataset files"""
        self._tmpdir = tempfile.TemporaryDirectory()
        self._dataset_lists = {}
        try:
            self._product_info = copernicusmarine.describe(
                show_all_versions=False,
                product_id=self.product_id,
                disable_progress_bar=True,
            ).products[0]
        except IndexError as error:
            raise RuntimeError(f"No product found with ID: {self.product_id}") from error

    def crawl(self):
        """Generator which crawls through a dataset repository and yields
        DatasetInfo objects
        """
        self.set_initial_state()
        for cmems_dataset in self._product_info.datasets:
            dataset_id = cmems_dataset.dataset_id
            dataset_variables = (cmems_dataset.versions[0].parts[0]
                                 .get_service_by_service_name('original-files').variables)
            if self.dataset_ids is None or dataset_id in self.dataset_ids:
                response = copernicusmarine.get(
                    dataset_id=dataset_id,
                    dry_run=True,
                    regex=self.make_filter(),
                    username=self.username,
                    password=self.password,
                    disable_progress_bar=True)
                for dataset_file in response.files:
                    yield DatasetInfo(
                        url=dataset_file.https_url,
                        metadata={
                            'cmems_dataset_name': cmems_dataset.dataset_name,
                            'variables': dataset_variables,
                            'product_info': self._product_info,
                        })
