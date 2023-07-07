# Generated by Django 4.0.4 on 2023-07-06 21:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0047_rename_channelconfigpermissions_channelconfigurationpermissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelpermission',
            name='group',
        ),
        migrations.RemoveField(
            model_name='modelpermission',
            name='permission',
        ),
        migrations.RemoveField(
            model_name='privatechat',
            name='connection',
        ),
        migrations.RemoveField(
            model_name='room',
            name='backlogs',
        ),
        migrations.RemoveField(
            model_name='room',
            name='connections',
        ),
        migrations.AddField(
            model_name='channel',
            name='backlogs',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='room', to='rooms.backloggroup'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='channel',
            name='room',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='rooms.room'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='ChannelConnection',
        ),
        migrations.DeleteModel(
            name='ModelPermission',
        ),
        migrations.DeleteModel(
            name='ModelPermissionGroup',
        ),
    ]
