# Generated by Django 4.0.4 on 2023-05-22 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reaction',
            name='image',
            field=models.ImageField(max_length=500, upload_to=''),
        ),
    ]
