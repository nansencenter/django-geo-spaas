"""Models for geospaas.processing"""
import json

import celery
import celery.canvas
from celery.result import AsyncResult
from django.db import models


from geospaas.catalog.models import Dataset

class ProcessingResult(models.Model):
    """Model used to keep track of processing result files"""

    class ProcessingResultType(models.TextChoices):
        """Possible type of results"""
        SYNTOOL = 'syntool', 'Syntool metadata file'
        IDF = 'idf', 'IDF file'

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    path = models.CharField(unique=True, max_length=500)
    type = models.CharField(max_length=20, choices=ProcessingResultType.choices)
    created = models.DateTimeField(auto_now_add=True)
    ttl = models.DurationField(default=None, null=True)


class Workflow(models.Model):
    name = models.CharField(max_length=100, unique=True)
    signature = models.JSONField()

    def run(self, *args, **kwargs):
        """This method should be used to create jobs.
        Should return a Job instance.
        """
        result = celery.signature(self.signature).delay(*args, **kwargs)
        return Job(task_id=result.task_id)


class Job(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    task_id = models.CharField(
        unique=True, max_length=255,
        help_text='ID of the last task in the job')
    date_created = models.DateTimeField(
        auto_now_add=True, db_index=True,
        verbose_name='Creation DateTime',
        help_text='Datetime: creation date of the job')

    def get_current_task_result(self):
        """Get the AsyncResult of the currently running task"""
        current_result = AsyncResult(self.task_id)
        finished = False
        while current_result.ready():
            try:
                current_result = current_result.children[0]
            except IndexError:
                finished = True
                break
        return current_result, finished
