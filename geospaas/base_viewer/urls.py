from django.urls import path

from geospaas.base_viewer.views import IndexView, get_geometry_geojson


app_name = 'base_viewer'
urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('geometry/<int:pk>', get_geometry_geojson, name='geometry_geojson'),
]
