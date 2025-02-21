from django.db import models

class Recipe(models.Model):
    name = models.CharField(max_length=255)
    image = models.URLField(blank=True, null=True)   
    cook_time = models.CharField(max_length=100, blank=True)
    servings = models.IntegerField(default=1)
    ingredients = models.TextField()
    instructions = models.TextField()

    def __str__(self):
        return self.name

