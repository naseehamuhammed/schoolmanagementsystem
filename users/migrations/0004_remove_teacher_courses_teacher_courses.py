# Generated by Django 5.1.3 on 2024-11-28 10:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_student_hobbies'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teacher',
            name='courses',
        ),
        migrations.AddField(
            model_name='teacher',
            name='courses',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assigned_teachers', to='users.course'),
        ),
    ]