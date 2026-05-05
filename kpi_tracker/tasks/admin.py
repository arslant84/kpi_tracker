from django.contrib import admin
from .models import Cycle, Goal, Task


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'start_date', 'end_date', 'is_active']
    list_editable = ['is_active']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['description', 'status', 'completion_level', 'base_deadline']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'weight', 'order']
    inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['description_short', 'goal', 'status', 'completion_level', 'base_deadline']
    list_filter = ['goal', 'status']
    list_editable = ['status', 'completion_level']

    def description_short(self, obj):
        return obj.description[:60]
    description_short.short_description = 'Description'
