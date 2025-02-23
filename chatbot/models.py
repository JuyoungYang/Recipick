from django.db import models

# from recipe.models import Recipe


class ChatLog(models.Model):
    user_input = models.TextField()
    recommended_recipes = models.TextField(blank=True, null=True)
    chosen_recipe = models.ForeignKey(
        "recipe.Recipe", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"ChatLog {self.id} - {self.created_at}"
