from pystac_client import Client

import geospaas.harvesting.arguments as arguments
from .base import Crawler, DatasetInfo


class STACCrawler(Crawler):
    """Crawler for STAC APIs"""
    name = 'stac'
    argument_parser = arguments.ArgumentParser([
        *Crawler.argument_parser.arguments.values(),
        arguments.StringArgument('url', required=True),
        arguments.SequenceArgument('collections', required=False, default=None,
                                   contents_type=arguments.StringArgument),
        arguments.DictArgument('filter', required=False, default=None),
        arguments.IntegerArgument('limit', default=100),
    ])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = kwargs['url']
        self.collections = kwargs['collections']
        self.filter = kwargs['filter']
        self.limit = kwargs['limit']
        self._client = Client.open(self.url, timeout=300)

    def crawl(self):
        items = self._client.search(
            collections=self.collections,
            intersects=self.location,
            datetime=self.time_range,
            filter=self.filter,
            limit=self.limit,
        ).items_as_dicts()

        for item in items:
            product = item['assets'].get('product') or item['assets'].get('Product')
            if product is None:
                raise ValueError("No URL found")
            yield DatasetInfo(url=product['href'], metadata=item)
