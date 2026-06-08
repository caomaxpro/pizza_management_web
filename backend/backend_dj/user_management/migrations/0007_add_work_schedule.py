# Generated manually for WorkSchedule model

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0006_add_role_change_log'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_start', models.DateField(help_text='ISO Monday of the week this schedule covers (YYYY-MM-DD)')),
                ('entries', models.JSONField(default=dict, help_text='Map of weekday to shift, e.g. {"mon": "08:00-16:00", "tue": "off"}')),
                ('notes', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(
                    help_text='Manager or Staff member this schedule applies to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='work_schedules',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_by', models.ForeignKey(
                    help_text='Admin/Manager who created this schedule',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_schedules',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-week_start', 'assigned_to'],
            },
        ),
        migrations.AddIndex(
            model_name='workschedule',
            index=models.Index(fields=['assigned_to', 'week_start'], name='usermgmt_ws_assigned_week_idx'),
        ),
        migrations.AddIndex(
            model_name='workschedule',
            index=models.Index(fields=['created_by', 'week_start'], name='usermgmt_ws_creator_week_idx'),
        ),
    ]
