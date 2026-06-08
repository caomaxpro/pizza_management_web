from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0007_add_work_schedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShiftTaskPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(max_length=3)),
                ('shift_start', models.CharField(max_length=5)),
                ('can_stock_take', models.BooleanField(default=False)),
                ('can_receive_stock', models.BooleanField(default=False)),
                ('work_schedule', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='shift_task_perms',
                    to='user_management.workschedule',
                )),
            ],
            options={
                'ordering': ['day', 'shift_start'],
                'unique_together': {('work_schedule', 'day', 'shift_start')},
            },
        ),
    ]
