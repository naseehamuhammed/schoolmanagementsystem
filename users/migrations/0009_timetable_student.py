# Generated by Django 5.1.3 on 2024-11-29 17:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_student_bus'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetable',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='timetables', to='users.student'),
        ),
    ]
