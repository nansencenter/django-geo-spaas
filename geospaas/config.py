class Config():
    """"""
    def __init__(self, settings):
        self.settings = settings

    def get_setting(self, section, key):
        """"""
        return self.settings[section][key]

config = Config({
    'base_viewer': {
        'apps': [
            {'label': 'Catalog', 'path': 'catalog/', 'urls': 'geospaas.catalog.urls'},
            {'label': 'Vocabularies', 'path': 'vocabularies/', 'urls': 'geospaas.vocabularies.urls'},
            {'label': 'Harvesting', 'path': 'harvesting/', 'urls': 'geospaas_harvesting.urls'},
        ]
    }
})
