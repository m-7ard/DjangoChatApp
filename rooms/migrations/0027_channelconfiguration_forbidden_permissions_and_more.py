# Generated by Django 4.0.4 on 2023-06-15 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('rooms', '0026_rename_permissions_channelconfiguration_allowed_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='channelconfiguration',
            name='forbidden_permissions',
            field=models.ManyToManyField(related_name='+', to='auth.permission'),
        ),
        migrations.AlterField(
            model_name='channelconfiguration',
            name='allowed_permissions',
            field=models.ManyToManyField(related_name='+', to='auth.permission'),
        ),
    ]
