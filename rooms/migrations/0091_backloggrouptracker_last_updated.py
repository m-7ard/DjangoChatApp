# Generated by Django 4.0.4 on 2023-08-23 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0090_remove_backloggrouptracker_last_checked_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='backloggrouptracker',
            name='last_updated',
            field=models.DateField(auto_now=True),
        ),
    ]
