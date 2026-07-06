# Generated manually for TimeEntry and TaskComment models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(blank=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('duration_minutes', models.PositiveIntegerField(default=0, help_text='Auto-calculated from start/end')),
                ('entry_type', models.CharField(choices=[('Regular', 'Regular'), ('Overtime', 'Overtime'), ('Billable', 'Billable'), ('Non-Billable', 'Non-Billable')], default='Regular', max_length=20)),
                ('is_billable', models.BooleanField(default=True)),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=0, help_text='Rate at time of entry', max_digits=18)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to='hr.employee')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to='projects.project')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to='projects.task')),
            ],
            options={
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='TaskComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('is_edited', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_comments', to='core.user')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='projects.taskcomment')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='projects.task')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
