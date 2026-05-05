from django.db import migrations, models
import django.db.models.deletion
from datetime import date


def create_default_cycle_and_assign(apps, schema_editor):
    Cycle = apps.get_model('tasks', 'Cycle')
    Goal = apps.get_model('tasks', 'Goal')
    cycle = Cycle.objects.create(
        name='2026 Performance Year',
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_active=True,
    )
    Goal.objects.all().update(cycle=cycle)


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_task_ai_insight_task_ai_insight_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-year', 'name'],
            },
        ),
        migrations.AddField(
            model_name='goal',
            name='cycle',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='goals',
                to='tasks.cycle',
            ),
        ),
        migrations.RunPython(create_default_cycle_and_assign, migrations.RunPython.noop),
    ]
