# Generated by Django 4.0.4 on 2023-08-04 12:31

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0079_alter_invite_expiry_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatechat',
            name='pinned_messages',
            field=models.ManyToManyField(blank=True, to='rooms.message'),
        ),
        migrations.AlterField(
            model_name='invite',
            name='expiry_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 5, 12, 31, 43, 27436, tzinfo=utc)),
        ),
    ]