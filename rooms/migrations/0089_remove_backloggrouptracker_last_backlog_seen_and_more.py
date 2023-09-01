# Generated by Django 4.0.4 on 2023-08-22 20:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0088_alter_backloggrouptracker_last_backlog_seen'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='backloggrouptracker',
            name='last_backlog_seen',
        ),
        migrations.AddField(
            model_name='backloggrouptracker',
            name='last_checked',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]