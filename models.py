from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
import datetime

# The sole data piece for TaskMaster - the task
class Task(models.Model):
    user = models.CharField(max_length=150)
    short_desc = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    due_time = models.TimeField(null=True, blank=True)
    long_desc = models.CharField(null=True, blank=True, max_length=2000)
    # Importance and Urgency are coded as 0-low, 1-medium, 2-high
    importance = models.IntegerField(null=False, blank=True, default=1,
        validators=[MaxValueValidator(2), MinValueValidator(0)])
    urgency = models.IntegerField(null=False, blank=True, default=1,
        validators=[MaxValueValidator(2), MinValueValidator(0)])
    completed = models.BooleanField(null=False, default=False)
    def __str__(self):
        return self.short_desc
    # Format the date for output to viewer
    @property
    def formatted_due_date(self):
        today = datetime.date.today()
        # Just use the weekday if within the next week
        if self.due_date == today - datetime.timedelta(days=1):
            return 'Yesterday'
        elif self.due_date == today:
            return 'Today'
        elif self.due_date == today + datetime.timedelta(days=1):
            return 'Tomorrow'
        # Use only the weekday if within the next week
        elif self.due_date > today and self.due_date < today + datetime.timedelta(days=7):
            return self.due_date.strftime('%a')
        # Omit the year if date is this year
        elif self.due_date.year == today.year:
            return self.due_date.strftime('%b %-d')
        else:
            return self.due_date.strftime('%x')
