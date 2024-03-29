# Generated by Django 4.0.4 on 2023-06-17 21:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('rooms', '0032_alter_room_options_room_guests_can_view_channels'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_pk', models.PositiveIntegerField(null=True)),
                ('value', models.CharField(blank=True, choices=[(True, 'True'), (False, 'False'), (None, 'None')], max_length=20, null=True)),
                ('channel_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='rooms.channelconfiguration')),
                ('target_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
        ),
        migrations.RemoveField(
            model_name='role',
            name='permissions',
        ),
        migrations.DeleteModel(
            name='ChannelConfigurationPermission',
        ),
    ]
