# Generated by Django 4.0.4 on 2023-06-18 12:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('rooms', '0033_modelpermission_remove_role_permissions_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelpermission',
            name='channel_config',
        ),
        migrations.AddField(
            model_name='modelpermission',
            name='permission',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
            preserve_default=False,
        ),
    ]
