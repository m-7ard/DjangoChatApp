from django.db import models


class Archive(models.Model):
    data = models.JSONField(default=dict)