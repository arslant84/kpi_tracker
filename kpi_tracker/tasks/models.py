from django.db import models
from datetime import date


class Cycle(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            Cycle.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Goal(models.Model):
    cycle = models.ForeignKey(
        Cycle, on_delete=models.CASCADE, related_name='goals', null=True, blank=True
    )
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#FFFF00')
    weight = models.FloatField(default=0)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.name

    @property
    def overall_completion(self):
        tasks = self.tasks.all()
        if not tasks.exists():
            return 0
        return round(sum(t.completion_level for t in tasks) / tasks.count())

    @property
    def status_counts(self):
        tasks = self.tasks.all()
        return {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'on_track': tasks.filter(status='on_track').count(),
            'behind': tasks.filter(status='behind').count(),
            'ahead': tasks.filter(status='ahead').count(),
            'not_started': tasks.filter(status='not_started').count(),
        }


class Task(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('on_track', 'On Track'),
        ('behind', 'Behind Schedule'),
        ('ahead', 'Ahead of Schedule'),
        ('completed', 'Completed'),
    ]

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    unit_of_measurement = models.TextField(blank=True)
    base_target = models.TextField(blank=True)
    stretch_target = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    base_deadline = models.DateField(null=True, blank=True)
    stretch_deadline = models.DateField(null=True, blank=True)
    completion_level = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    notes = models.TextField(blank=True, help_text='Progress update and what is pending')
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.goal.name} – {self.description[:60]}"

    @property
    def days_until_deadline(self):
        if not self.base_deadline:
            return None
        from datetime import date
        return (self.base_deadline - date.today()).days

    @property
    def is_overdue(self):
        days = self.days_until_deadline
        return days is not None and days < 0 and self.status != 'completed'

    @property
    def is_in_progress(self):
        return 0 < self.completion_level < 100 and self.status != 'completed'


class TaskUpdate(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='updates')
    note = models.TextField(blank=True)
    completion_level = models.IntegerField()
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task.description[:40]} @ {self.created_at:%Y-%m-%d %H:%M}"
