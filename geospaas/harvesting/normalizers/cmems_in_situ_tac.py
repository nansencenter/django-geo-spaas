"""Normalizer for the Copernicus In Situ TAC metadata convention"""
import dateutil.parser

import geospaas.harvesting.normalizers.utils as utils

from .base import MetadataNormalizer


class CMEMSInSituTACMetadataNormalizer(MetadataNormalizer):
    """Generate the properties of a GeoSPaaS Dataset using
    CMEMS In Situ TAC attributes
    """

    name = 'cmems_in_situ'

    @utils.raises(KeyError)
    def get_entry_title(self, dataset_info):
        return dataset_info.metadata['title']

    @utils.raises(KeyError)
    def get_entry_id(self, dataset_info):
        return dataset_info.metadata['id']

    def get_summary(self, dataset_info):
        """Get the dataset's summary if it is available in the
        metadata, otherwise use a default
        """
        description = None
        raw_summary = dataset_info.metadata.get('summary')
        url = dataset_info.url

        if raw_summary and raw_summary.strip():
            description = raw_summary

        if 'INSITU_GLO_NRT_OBSERVATIONS_013_030' in url:
            product = 'INSITU_GLO_NRT_OBSERVATIONS_013_030'
            if not description:
                description = (
                    'Global Ocean - near real-time (NRT) in situ quality controlled '
                    'observations, hourly updated and distributed by INSTAC within 24-48 hours '
                    'from acquisition in average. Data are collected mainly through global '
                    'networks (Argo, OceanSites, GOSUD, EGO) and through the GTS'
                )
        elif 'INSITU_GLO_UV_NRT_OBSERVATIONS_013_048' in url:
            product = 'INSITU_GLO_UV_NRT_OBSERVATIONS_013_048'
            if not description:
                description = (
                    'This product is entirely dedicated to ocean current data observed in '
                    'near-real time. Surface current data from 2 different types of instruments'
                    ' are distributed: velocities calculated along the trajectories of drifting'
                    ' buoys from the DBCP’s Global Drifter Program, and velocities measured by '
                    'High Frequency radars from the European High Frequency radar Network'
                )
        else:
            product = utils.UNKNOWN
            if not description:
                description = 'CMEMS in situ TAC data'

        return utils.dict_to_string({
            utils.SUMMARY_FIELDS['description']: description or '',
            utils.SUMMARY_FIELDS['processing_level']: '2',
            utils.SUMMARY_FIELDS['product']: product
        })

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_start(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['time_coverage_start'])

    @utils.raises((KeyError, dateutil.parser.ParserError))
    def get_time_coverage_end(self, dataset_info):
        return dateutil.parser.parse(dataset_info.metadata['time_coverage_end'])

    def get_keywords(self, dataset_info):
        return utils.find_keywords((
            {
                'kind': 'gcmd_platform',
                'data__Basis': 'Water-based Platforms',
                'data__Category': '',
                'data__Long_Name': '',
                'data__Short_Name': '',
                'data__Sub_Category': '',
            },
            {
                'kind': 'gcmd_instrument',
                'data__Type': '',
                'data__Class': '',
                'data__Subtype': '',
                'data__Category': 'In Situ/Laboratory Instruments',
                'data__Long_Name': '',
                'data__Short_Name': '',
            },
            {'kind': 'gcmd_provider', 'data__icontains': 'cmems'},
            {'kind': 'iso19115_topic_category', 'data__icontains': 'Oceans'},
        ))

    @utils.raises(KeyError)
    def get_location_geometry(self, dataset_info):
        candidates = ('geometry', 'location_geometry')
        for attribute_name in candidates:
            try:
                return dataset_info.metadata[attribute_name]
            except KeyError:
                continue
