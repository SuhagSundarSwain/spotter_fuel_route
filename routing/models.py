from django.db import models

# Create your models here.
class FuelStation(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    retail_price  = models.FloatField()
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)

    def __str__(self):
        return f"{self.name}, {self.city}, {self.state}"