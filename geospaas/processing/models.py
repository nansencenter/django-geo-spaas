"""Models for geospaas.processing"""
import json

import celery
import celery.result
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
    _signature = models.JSONField()

    @classmethod
    def from_signature(cls, name, signature):
        """Create a workflow from a Celery Signature object.
        Groups of tasks are not supported"""
        return cls.objects.create(name=name, _signature=signature)

    @property
    def signature(self):
        return celery.signature(self._signature)

    def run(self, *args, **kwargs):
        """This method should be used to create jobs.
        Should return a Job instance.
        """
        result = celery.signature(self.signature).delay(*args, **kwargs)
        job = Job.from_result(workflow=self, celery_result=result)
        job.save()
        return job


class Job(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    _result_ref = models.JSONField(unique=True)
    date_created = models.DateTimeField(
        auto_now_add=True, db_index=True,
        verbose_name='Creation DateTime',
        help_text='Datetime: creation date of the job')

    @classmethod
    def from_result(cls, workflow: Workflow, celery_result: celery.result.ResultBase):
        job = Job(workflow=workflow, _result_ref=celery_result.as_tuple())
        job._result_info = None
        return job

    @property
    def result_info(self):
        if self._result_info is None:
            self._result_info = celery.result.result_from_tuple(self._result_ref)
        return self._result_info

    @property
    def state(self):
        try:
            return self.result_info.state
        except AttributeError:
            return [r.state for r in self.result_info.results]

    def ready(self):
        return self.result_info.ready()

    def successful(self):
            return self.result_info.successful()

    def failed(self):
            return self.result_info.failed()

    def get(self):
            return self.result_info.get()
