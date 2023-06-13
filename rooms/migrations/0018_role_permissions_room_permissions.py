# Generated by Django 4.0.4 on 2023-06-12 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('rooms', '0017_remove_role_permissions_remove_room_permissions_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(to='auth.permission'),
        ),
        migrations.AddField(
            model_name='room',
            name='permissions',
            field=models.ManyToManyField(to='auth.permission'),
        ),
    ]
