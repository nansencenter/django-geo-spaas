# App for exporting metadata to GCMD DIF format

The following fields are not in the Dataset model, and should be added by the
export-DIF app.

See http://gcmd.nasa.gov/add/difguide/index.html for reference.

## Required fields

```
metadata_name = models.CharField(max_length=50, default='CEOS IDN DIF')
metadata_version = models.CharField(max_length=50, default='VERSION 9.9')
```

## Highly recommended fields

* data_set_citation's

```
personnel = models.ForeignKey(Personnel, blank=True, null=True) # = contact person
```

* paleo_temporal_coverage (if needed)
* spatial_coverage 
* data_resolution
* project
* quality
* use_constraints
* distribution_media
* distribution_size
* distribution_format
* distribution_fee
* language (Language list in  the ISO 639 language codes: http://www.loc.gov/standards/iso639-2/php/code_list.php)
* progress
* related_url

## Recommended fields

* DIF_revision_history
* originating_center
* references
* parent_DIF (this can be generated from the DatasetRelationship model)
* IDN_node
* DIF_creation_date
* last_DIF_revision_date
* future_DIF_review_date
* privacy_status (True or False)
* extended_metadata

```
# TO APP FOR EXPORTING DIF
class DIFRevisionHistoryItem(models.Model):
    dataset = models.ForeignKey(Dataset)
    date = models.DateField()
    text = models.TextField()
```

```
class DatasetCitation(models.Model):
    dataset = models.ForeignKey(Dataset)
    dataset_creator = models.ForeignKey(Personnel)
    dataset_editor = models.ForeignKey(Personnel)
    dataset_publisher = models.ForeignKey(DataCenter)
    #dataset_title = models.CharField(max_length=220) # Same as entry_title in Dataset
    dataset_series_name = models.CharField(max_length=220)
    dataset_release_date = models.DateField()
    dataset_release_place = models.CharField(max_length=80)
    version = models.Charfield(max_length=15)
    issue_identification = models.CharField(max_length=80)
    data_presentation_form = models.CharField(max_length=80)
    other_citation_details = models.CharField(max_length=220)
    dataset_DOI = models.CharField(max_length=220)
    online_resource = models.URLField(max_length=600)

    def __str__(self):
        return self.dataset_DOI
```
    


