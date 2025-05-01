from django.db import models

class Dish(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    ingredients = models.TextField()
    cuisine_type = models.CharField(max_length=100, blank=True, null=True)
    spiciness_level = models.IntegerField(blank=True, null=True)
    suitable_for_diet = models.CharField(max_length=200, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name