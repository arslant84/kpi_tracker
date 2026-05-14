from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('table/', views.kpi_table, name='kpi_table'),

    # Cycles
    path('cycles/', views.cycle_list, name='cycle_list'),
    path('cycles/add/', views.add_cycle, name='add_cycle'),
    path('cycles/<int:cycle_id>/edit/', views.edit_cycle, name='edit_cycle'),
    path('cycles/<int:cycle_id>/delete/', views.delete_cycle, name='delete_cycle'),
    path('cycles/<int:cycle_id>/switch/', views.switch_cycle, name='switch_cycle'),

    # Goals
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/<int:goal_id>/edit/', views.edit_goal, name='edit_goal'),
    path('goals/<int:goal_id>/delete/', views.delete_goal, name='delete_goal'),
    path('goals/<int:goal_id>/add-task/', views.add_task, name='add_task_to_goal'),
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:task_id>/status/', views.update_status, name='update_status'),
    path('tasks/<int:task_id>/updates/<int:update_id>/delete/', views.delete_update, name='delete_update'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
]
