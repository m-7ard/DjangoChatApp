# Generated by Django 4.0.4 on 2023-06-18 18:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0035_modelpermissiongroup_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channelconfiguration',
            name='permissions',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='channel_configuration', to='rooms.modelpermissiongroup'),
        ),
        migrations.AlterField(
            model_name='role',
            name='permissions',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='role', to='rooms.modelpermissiongroup'),
        ),
    ]
