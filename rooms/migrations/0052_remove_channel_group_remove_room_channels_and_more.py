# Generated by Django 4.0.4 on 2023-07-08 20:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0051_chatter_group_alter_channel_backlogs_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='channel',
            name='group',
        ),
        migrations.RemoveField(
            model_name='room',
            name='channels',
        ),
        migrations.AddField(
            model_name='channel',
            name='room',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='rooms.room'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='backlogs',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='channel', to='rooms.backloggroup'),
        ),
        migrations.AlterField(
            model_name='chatter',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='values', to='rooms.chattergroup'),
        ),
        migrations.AlterField(
            model_name='room',
            name='default_role',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='rooms.role'),
        ),
        migrations.DeleteModel(
            name='ChannelGroup',
        ),
    ]