from django.db import models

class SourceManager(models.Manager):

    def get_by_natural_key(self, p, i):
        return self.get(platform__short_name=p, instrument__short_name=i)

