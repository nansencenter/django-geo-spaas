# basic viewer of geospaas

This is the app for showing the basic viewer of geospass as the geospaas GUI.
By using this GUI, visitor (user) can accomplish the basic filtering for ingested datasets.

This can be done by different forms that are available for this purpose:

> `leaflet field` which can be used for spatial filtering

> `time coverage start field ` which can be used for filtering base on start time of dataset

> `time coverage end field ` which can be used for filtering base on ending time of dataset

> `Source field ` which can be used for filtering based on the source of the dataset




Usage
-----
`time coverage start` is searchable timedate specification in UTC

`time coverage end` is searchable timedate specification in UTC

The url version of datasets after filtering are shown in the right side of the page.

Quick start for developers
--------------------------

1. Obtain the geospaas in your machine by clone the whole repo of geospaas.

2. open your browser with `localhost:8080/base/` after running the runserver command of django
