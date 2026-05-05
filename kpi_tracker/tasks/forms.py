from django import forms
from .models import Cycle, Goal, Task, TaskUpdate


class CycleForm(forms.ModelForm):
    class Meta:
        model = Cycle
        fields = ['name', 'year', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026 Performance Year'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'color', 'weight', 'order']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.1'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'goal', 'description', 'unit_of_measurement',
            'base_target', 'stretch_target',
            'start_date', 'base_deadline', 'stretch_deadline',
            'completion_level', 'status', 'notes',
        ]
        widgets = {
            'goal': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'unit_of_measurement': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'base_target': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'stretch_target': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Progress update, what has been done, what is still pending...'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'base_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'stretch_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'completion_level': forms.NumberInput(attrs={'min': 0, 'max': 100, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class TaskStatusForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['completion_level', 'status', 'notes']
        widgets = {
            'completion_level': forms.NumberInput(attrs={'min': 0, 'max': 100, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'What was done? What is still pending?'}),
        }


class TaskUpdateForm(forms.Form):
    """Standalone form for logging a new progress update entry."""
    completion_level = forms.IntegerField(
        min_value=0, max_value=100,
        widget=forms.NumberInput(attrs={'min': 0, 'max': 100, 'class': 'form-control'}),
    )
    status = forms.ChoiceField(
        choices=Task.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'What was done? What is still pending? Any blockers?',
        }),
    )
