# Generated by Django 4.0.4 on 2023-06-15 14:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0025_alter_room_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='channelconfiguration',
            old_name='permissions',
            new_name='allowed_permissions',
        ),
    ]
