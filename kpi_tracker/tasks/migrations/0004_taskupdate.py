from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_cycle_goal_cycle'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField(blank=True)),
                ('completion_level', models.IntegerField()),
                ('status', models.CharField(
                    choices=[
                        ('not_started', 'Not Started'),
                        ('on_track', 'On Track'),
                        ('behind', 'Behind Schedule'),
                        ('ahead', 'Ahead of Schedule'),
                        ('completed', 'Completed'),
                    ],
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='updates',
                    to='tasks.task',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
