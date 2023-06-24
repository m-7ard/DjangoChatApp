# Generated by Django 4.0.4 on 2023-06-18 14:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0034_remove_modelpermission_channel_config_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelPermissionGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.RemoveField(
            model_name='modelpermission',
            name='target_pk',
        ),
        migrations.RemoveField(
            model_name='modelpermission',
            name='target_type',
        ),
        migrations.AddField(
            model_name='channelconfiguration',
            name='permissions',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='channel_configuration', to='rooms.modelpermissiongroup'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='modelpermission',
            name='group',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='rooms.modelpermissiongroup'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='role',
            name='permissions',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='role', to='rooms.modelpermissiongroup'),
            preserve_default=False,
        ),
    ]