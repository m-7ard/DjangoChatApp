# Generated by Django 4.0.4 on 2023-07-17 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0058_channel_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupchat',
            name='image',
            field=models.ImageField(max_length=500, upload_to=''),
        ),
    ]