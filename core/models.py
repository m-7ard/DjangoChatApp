from django.db import models
from django.utils import timezone

from users.models import CustomUser


class News(models.Model):
    title = models.CharField(blank=False, max_length=100)
    content = models.TextField(blank=False)
    author = models.ForeignKey(CustomUser, related_name='authored', on_delete=models.CASCADE, blank=False, null=True)
    date_posted = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "News"
        
    def day_month_year(self):
        return self.date_posted.strftime("%d.%m.%y")

    def hour_minute_second(self):
        return self.date_posted.strftime("%H:%M:%S")

    def __str__(self):
        return self.title