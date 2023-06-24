# Generated by Django 4.0.4 on 2023-06-09 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0010_remove_log_icon_action_icon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='can_delete_own_message',
        ),
        migrations.RemoveField(
            model_name='role',
            name='can_edit_own_message',
        ),
        migrations.AddField(
            model_name='role',
            name='default',
            field=models.BooleanField(default=False),
        ),
    ]