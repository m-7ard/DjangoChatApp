# Generated by Django 4.0.4 on 2023-08-04 12:14

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0077_alter_invite_expiry_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='backloggroup',
            name='private_channel',
        ),
        migrations.AddField(
            model_name='backloggroup',
            name='private_chat',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='backlog_group', to='rooms.privatechat'),
        ),
        migrations.AlterField(
            model_name='backloggroup',
            name='kind',
            field=models.CharField(choices=[('group_channel', 'Group Chat Backlogs'), ('private_chat', 'Private Chat Backlogs')], max_length=20),
        ),
        migrations.AlterField(
            model_name='invite',
            name='expiry_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 5, 12, 14, 37, 325194, tzinfo=utc)),
        ),
        migrations.DeleteModel(
            name='PrivateChannel',
        ),
    ]