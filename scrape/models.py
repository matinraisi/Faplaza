from django.db import models
import uuid

class ScrapeData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(unique=True, default='')
    color = models.JSONField(null=True, blank=True, default=list)
    size = models.JSONField(null=True, blank=True, default=list)
    style = models.JSONField(null=True, blank=True, default=list)
    flavor = models.JSONField(null=True, blank=True, default=list)
    response_data = models.JSONField()
    price = models.CharField(max_length=255, null=True, blank=True)
    images = models.JSONField(null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    available = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return str(self.id)
