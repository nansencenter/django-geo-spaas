Extending Django-Geo-SPaaS
==========================

Django-Geo-SPaaS defines the basic data model of Geo-SPaaS, following the DIF and GCMD keywords
standards. It also contains a sub-package **nansat_ingestor** which is used to ingest any dataset
that can be opened with `Nansat <https://github.com/nansencenter/nansat>`_.

The generic **geospaas** package, however, needs to be extended in many cases. For example, `Nansat
<https://github.com/nansencenter/nansat>`_ only handles raster data. Point or trajectory measurements
therefore need their own ingestors. Also, some datasets contain extra metadata not covered by the
standards. This makes it necessary to extend the main data model.

This section describes how to add new Geo-SPaaS packages that extends django-geo-spaas.

Naming convention
-----------------

The git repository of the new application should be prefixed by **django-geo-spaas-**. This way, it
will be clear for everyone what it is. The actual package extending **geospaas** should be named
according to the dataset under consideration.

Data model
----------

The simplest Geo-SPaaS packages need to have a customized `get_or_create` method in their manager and
a new `ingest command`. This is quite easy to handle by making a new `Dataset` proxy model with its
own field `objects` pointing to the new manager.

This is done as follows:

.. code-block:: python
   :caption: models.py

    from django.db import models
    from geospaas.catalog.models import Dataset as CatalogDataset

    from some_new_package.managers import SomeNewManager
   
    class Dataset(CatalogDataset):
        class Meta:
            proxy = True

        objects = SomeNewManager()

.. code-block:: python
   :caption: managers.py

    from django.db import models

    class SomeNewManager(models.Manager):

        def get_or_create(self, uri, *args, **kwargs):

            <code to add dataset in the geospaas catalog>

.. code-block:: python
   :caption: management/commands/ingest_new_dataset_type.py

    from some_new_package.models import Dataset

    class Command(NansatIngestor):
        help = 'Add some_new_package file to catalog archive'

        def handle(self, *args, **options):
            # Note: this is a simplified example...
            non_ingested_uris, nansat_options = self._get_args(*args, **options)

            for non_ingested_uri in non_ingested_uris:
                self.stdout.write('Ingesting %s ...\n' % non_ingested_uri)
                ds, cr = Dataset.objects.get_or_create(non_ingested_uri, **nansat_options)

For datasets of which extra metadata is required, we need to create a new model `ExtraMetadata` with
a foreignkey to the dataset, e.g.:

.. code-block:: python
   :caption: models.py - with an extra model

    class ExtraMetadata(models.Model):

        class Meta:
            unique_together = (("dataset", "metadata_field"))

        dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
        metadata_field = models.CharField(default='', max_length=100)

This model should be populated by the new manager (e.g., `NewManager`) when a `Dataset` is added. To
avoid recursive import, the `ExtraMetadata` class must be imported inline in `get_or_create` (unless
someone knows a better solution), e.g.:

.. code-block:: python
   :caption: managers.py - also adding ExtraMetadata in get_or_create
   :emphasize-lines: 10

    from geospaas.nansat_ingestor.managers import DatasetManager

    class SomeNewManager(DatasetManager):

        def get_or_create(self, uri, *args, **kwargs):

            ds, created = super(ScatManager, self).get_or_create(uri, *args, **kwargs)
            if created:
                # Import ExtraMetata model here to avoid recursion
                from some_new_package.models import ExtraMetadata
                # Store the new metadata and associate the dataset
                extra, _ = ExtraMetadata.objects.get_or_create(dataset=ds, metadata_field='something')
                if not _:
                    raise ValueError('Created new dataset but could not create instance of ExtraMetadata')
                ds.extrametadata_set.add(extra)

            return ds, created

And finally, remember to test...

.. code-block:: python
   :caption: tests.py

    class ScatterometerModelTests(TestCase):

        # Assert that only one ExtraMetadata instance can be created when a given Dataset is added
        def test_unique_together(self):
            pass

        # and more tests...

    class NewManagerTests(TestCase):

        @mock.patch('django.db.models.manager.Manager.get_or_create')
        @mock.patch('some_new_package.managers.DatasetManager.get_or_create')
        def test_get_or_create(self, mock_ds_get_or_create, mock_db_get_or_create):
            mock_dataset = mock.Mock(spec=Dataset)
            mock_extra_metadata = mock.Mock(spec=ExtraMetadata)
            mock_ds_get_or_create.return_value = (mock_dataset, True)
            mock_db_get_or_create.return_value = (mock_extra_metadata, True)
            uri = 'some_filename'
            result = Dataset.objects.get_or_create(uri)
            mock_ds_get_or_create.assert_called_with(uri, max_uris_len=4, n_points=1000, quartile=0)
            mock_db_get_or_create.assert_called_with(dataset=mock_dataset, quartile=0)
            mock_dataset.extrametadata_set.add.assert_called_with(mock_extra_metadata)
            self.assertEqual(result, (mock_dataset, True))

    class IngestScatCommandTests(TestCase):
        pass



