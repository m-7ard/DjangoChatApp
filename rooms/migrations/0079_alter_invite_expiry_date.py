# Generated by Django 4.0.4 on 2023-08-04 12:26

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0078_remove_backloggroup_private_channel_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='expiry_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 5, 12, 26, 58, 293752, tzinfo=utc)),
        ),
    ]