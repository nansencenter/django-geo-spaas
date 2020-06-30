from django.urls import path
from django.conf.urls import include

urlpatterns = [
    path('tests/', include('geospaas.base_viewer.urls'))
]
