"""
Long running tasks to be executed by Celery workers.
All tasks that act on a geospaas dataset (so all the tasks defined here) should:
  - take as argument a tuple which first element is the dataset's ID.
  - return a tuple whose first element is the dataset ID.
If the task also acts on files related to a dataset, it should be decorated
with `lock_dataset_files`.
"""
import celery
import celery.contrib.django.task

from geospaas.config import plugins_manager


class GeoSPaaSTask(celery.contrib.django.task.DjangoTask):
    """"""
    def __init__(self, *args, **kwargs):
        self.inputs = kwargs.pop('inputs', None)
        self.outputs = kwargs.pop('outputs', None)
        super().__init__(*args, **kwargs)

app = celery.Celery('geospaas.processing', task_cls='geospaas.processing.tasks:GeoSPaaSTask')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(plugins_manager.plugins)
