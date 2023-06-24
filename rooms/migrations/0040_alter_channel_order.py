# Generated by Django 4.0.4 on 2023-06-24 18:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0039_remove_room_guests_can_view_channels'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='order',
            field=models.PositiveIntegerField(default=100, validators=[django.core.validators.MaxValueValidator(1000000), django.core.validators.MinValueValidator(1)]),
        ),
    ]