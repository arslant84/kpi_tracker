from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.utils import timezone
from datetime import date
from .models import Cycle, Goal, Task, TaskUpdate
from .forms import CycleForm, GoalForm, TaskForm, TaskStatusForm, TaskUpdateForm
def _get_active_cycle(request):
    cycle_id = request.session.get('active_cycle_id')
    if cycle_id:
        try:
            return Cycle.objects.get(id=cycle_id)
        except Cycle.DoesNotExist:
            pass
    cycle = Cycle.objects.filter(is_active=True).first() or Cycle.objects.order_by('-year').first()
    if cycle:
        request.session['active_cycle_id'] = cycle.id
    return cycle


def _gantt_pct(d, start, days):
    if not d:
        return None
    return round(max(0, min(100, (d - start).days / days * 100)), 2)


def _gantt_width(start_d, end_d, gantt_start, gantt_days):
    if not start_d or not end_d:
        return None
    left = _gantt_pct(start_d, gantt_start, gantt_days)
    return round(max(1, min(100 - left, (end_d - start_d).days / gantt_days * 100)), 2)


@login_required
def dashboard(request):
    cycle = _get_active_cycle(request)

    if not cycle:
        return render(request, 'tasks/dashboard.html', {'no_cycle': True})

    goals = Goal.objects.filter(cycle=cycle).prefetch_related('tasks')
    tasks_qs = Task.objects.filter(goal__cycle=cycle)

    total_tasks = tasks_qs.count()
    total_goals = goals.count()

    completed = tasks_qs.filter(status='completed').count()
    on_track = tasks_qs.filter(status='on_track').count()
    behind = tasks_qs.filter(status='behind').count()
    ahead = tasks_qs.filter(status='ahead').count()
    not_started = tasks_qs.filter(status='not_started').count()

    overall_completion = 0
    if total_tasks:
        overall_completion = round(tasks_qs.aggregate(avg=Avg('completion_level'))['avg'] or 0)

    today = timezone.now().date()
    overdue_tasks = (
        tasks_qs.filter(base_deadline__lt=today)
        .exclude(status='completed')
        .select_related('goal')
        .order_by('base_deadline')
    )
    in_progress_tasks = (
        tasks_qs.filter(completion_level__gt=0, completion_level__lt=100)
        .exclude(status='completed')
        .select_related('goal')
        .order_by('base_deadline')
    )

    gantt_start = cycle.start_date
    gantt_end = cycle.end_date
    gantt_days = max((gantt_end - gantt_start).days, 1)

    gantt_months = []
    year = cycle.year
    for m in range(1, 13):
        try:
            d = date(year, m, 1)
            if gantt_start <= d <= gantt_end:
                gantt_months.append({
                    'name': d.strftime('%b'),
                    'left': round((d - gantt_start).days / gantt_days * 100, 2),
                })
        except ValueError:
            pass

    today_left = _gantt_pct(today, gantt_start, gantt_days)

    gantt_rows = []
    for goal in goals:
        for task in goal.tasks.all():
            if task.start_date and task.base_deadline:
                left = _gantt_pct(task.start_date, gantt_start, gantt_days)
                width = _gantt_width(task.start_date, task.base_deadline, gantt_start, gantt_days)
                gantt_rows.append({
                    'task': task,
                    'goal': goal,
                    'left': left,
                    'width': width,
                })

    context = {
        'cycle': cycle,
        'goals': goals,
        'total_goals': total_goals,
        'total_tasks': total_tasks,
        'overall_completion': overall_completion,
        'completed': completed,
        'on_track': on_track,
        'behind': behind,
        'ahead': ahead,
        'not_started': not_started,
        'overdue_tasks': overdue_tasks,
        'in_progress_tasks': in_progress_tasks,
        'gantt_months': gantt_months,
        'today_left': today_left,
        'gantt_rows': gantt_rows,
        'has_gantt': len(gantt_rows) > 0,
        'today': today,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def kpi_table(request):
    cycle = _get_active_cycle(request)
    if not cycle:
        return render(request, 'tasks/task_list.html', {'goals': [], 'no_cycle': True})
    goals = Goal.objects.filter(cycle=cycle).prefetch_related('tasks')
    total_weight = round(sum(g.weight for g in goals), 1)
    return render(request, 'tasks/task_list.html', {
        'goals': goals,
        'cycle': cycle,
        'total_weight': total_weight,
        'remaining_weight': round(100 - total_weight, 1),
        'over_weight': round(total_weight - 100, 1) if total_weight > 100 else 0,
    })


# ── Cycle CRUD ──────────────────────────────────────────────────────────────

@login_required
def cycle_list(request):
    cycles = Cycle.objects.all()
    return render(request, 'tasks/cycle_list.html', {'cycles': cycles})


@login_required
def add_cycle(request):
    form = CycleForm(request.POST or None)
    if form.is_valid():
        cycle = form.save()
        request.session['active_cycle_id'] = cycle.id
        messages.success(request, f'Cycle "{cycle.name}" created and set as active.')
        return redirect('cycle_list')
    return render(request, 'tasks/cycle_form.html', {'form': form, 'title': 'New Cycle'})


@login_required
def edit_cycle(request, cycle_id):
    cycle = get_object_or_404(Cycle, id=cycle_id)
    form = CycleForm(request.POST or None, instance=cycle)
    if form.is_valid():
        form.save()
        messages.success(request, 'Cycle updated.')
        return redirect('cycle_list')
    return render(request, 'tasks/cycle_form.html', {'form': form, 'title': 'Edit Cycle', 'cycle': cycle})


@login_required
def delete_cycle(request, cycle_id):
    cycle = get_object_or_404(Cycle, id=cycle_id)
    if request.method == 'POST':
        if request.session.get('active_cycle_id') == cycle.id:
            del request.session['active_cycle_id']
        cycle.delete()
        messages.success(request, 'Cycle deleted.')
        return redirect('cycle_list')
    return render(request, 'tasks/delete_cycle.html', {'cycle': cycle})


@login_required
def switch_cycle(request, cycle_id):
    cycle = get_object_or_404(Cycle, id=cycle_id)
    request.session['active_cycle_id'] = cycle.id
    messages.success(request, f'Switched to "{cycle.name}".')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# ── Goal CRUD ────────────────────────────────────────────────────────────────

def _weight_context(cycle, exclude_goal=None):
    """Return weight breakdown for all goals in a cycle (optionally excluding one)."""
    qs = Goal.objects.filter(cycle=cycle)
    if exclude_goal:
        qs = qs.exclude(id=exclude_goal.id)
    goals = list(qs.order_by('order', 'id'))
    allocated = round(sum(g.weight for g in goals), 1)
    return {
        'weight_goals': goals,
        'allocated_weight': allocated,
        'remaining_weight': round(100 - allocated, 1),
    }


@login_required
def add_goal(request):
    cycle = _get_active_cycle(request)
    if not cycle:
        messages.error(request, 'Create a cycle first before adding goals.')
        return redirect('cycle_list')
    form = GoalForm(request.POST or None)
    if form.is_valid():
        goal = form.save(commit=False)
        goal.cycle = cycle
        goal.save()
        messages.success(request, 'Goal added.')
        return redirect('kpi_table')
    ctx = {'form': form, 'title': 'Add Goal', 'cycle': cycle}
    ctx.update(_weight_context(cycle))
    return render(request, 'tasks/goal_form.html', ctx)


@login_required
def edit_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    form = GoalForm(request.POST or None, instance=goal)
    if form.is_valid():
        form.save()
        messages.success(request, 'Goal updated.')
        return redirect('kpi_table')
    ctx = {'form': form, 'title': 'Edit Goal', 'goal': goal, 'cycle': goal.cycle}
    ctx.update(_weight_context(goal.cycle, exclude_goal=goal))
    return render(request, 'tasks/goal_form.html', ctx)


@login_required
def delete_goal(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if request.method == 'POST':
        goal.delete()
        messages.success(request, 'Goal and all its tasks deleted.')
        return redirect('kpi_table')
    return render(request, 'tasks/delete_goal.html', {'goal': goal})


# ── Task CRUD ────────────────────────────────────────────────────────────────

@login_required
def add_task(request, goal_id=None):
    cycle = _get_active_cycle(request)
    initial = {}
    if goal_id:
        initial['goal'] = get_object_or_404(Goal, id=goal_id)
    form = TaskForm(request.POST or None, initial=initial)
    if cycle:
        form.fields['goal'].queryset = Goal.objects.filter(cycle=cycle)
    if form.is_valid():
        form.save()
        messages.success(request, 'Task added.')
        return redirect('kpi_table')
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Add Task', 'cycle': cycle})


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    form = TaskForm(request.POST or None, instance=task)
    form.fields['goal'].queryset = Goal.objects.filter(cycle=task.goal.cycle)
    if form.is_valid():
        form.save()
        messages.success(request, 'Task updated.')
        return redirect('kpi_table')
    return render(request, 'tasks/task_form.html', {
        'form': form, 'title': 'Edit Task', 'task': task, 'cycle': task.goal.cycle
    })


@login_required
def update_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == 'POST':
        form = TaskUpdateForm(request.POST)
        if form.is_valid():
            cl = form.cleaned_data['completion_level']
            st = form.cleaned_data['status']
            note = form.cleaned_data['note']
            # Save to history
            TaskUpdate.objects.create(
                task=task,
                completion_level=cl,
                status=st,
                note=note,
            )
            # Update the task itself (notes = latest entry for KPI table)
            Task.objects.filter(id=task.id).update(
                completion_level=cl,
                status=st,
                notes=note,
            )
            messages.success(request, 'Update logged.')
            return redirect('update_status', task_id=task.id)
    else:
        form = TaskUpdateForm(initial={
            'completion_level': task.completion_level,
            'status': task.status,
        })

    updates = task.updates.all()
    return render(request, 'tasks/update_status.html', {
        'form': form,
        'task': task,
        'updates': updates,
    })


@login_required
def delete_update(request, task_id, update_id):
    update = get_object_or_404(TaskUpdate, id=update_id, task_id=task_id)
    if request.method == 'POST':
        update.delete()
        messages.success(request, 'Update entry deleted.')
    return redirect('update_status', task_id=task_id)


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect('kpi_table')
    return render(request, 'tasks/delete_task.html', {'task': task})
