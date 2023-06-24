# Generated by Django 4.0.4 on 2023-06-13 12:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0019_remove_channel_visible_to_channelconfiguration_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='room',
            name='permissions',
        ),
        migrations.AddField(
            model_name='room',
            name='default_role',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='rooms.role'),
        ),
    ]