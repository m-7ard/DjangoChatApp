# Generated by Django 4.0.4 on 2023-06-15 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0024_room_public'),
    ]

    operations = [
        migrations.AlterField(
            model_name='room',
            name='description',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
