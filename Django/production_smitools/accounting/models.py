from django.db import models

class Providers(models.Model):
    client = models.CharField(max_length=20)
    name = models.CharField(max_length=100)

class ProvidersFiles(models.Model):
    provider_id = models.ForeignKey('Providers', on_delete=models.CASCADE)
    client = models.CharField(max_length=20)
    month = models.IntegerField()
    local_file = models.CharField(max_length=8000, null=True)
    sharefile_folder = models.CharField(max_length=8000, null=True)
    published_file = models.CharField(max_length=8000, null=True)
