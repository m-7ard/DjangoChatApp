# Generated by Django 4.2.6 on 2023-10-15 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0128_message_attachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emoji',
            name='image',
            field=models.ImageField(upload_to=''),
        ),
    ]
