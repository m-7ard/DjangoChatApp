# Generated by Django 4.0.4 on 2023-07-06 14:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0046_rename_channel_privatechat_connection_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ChannelConfigPermissions',
            new_name='ChannelConfigurationPermissions',
        ),
    ]
