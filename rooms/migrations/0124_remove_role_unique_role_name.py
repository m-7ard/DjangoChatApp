# Generated by Django 4.0.4 on 2023-10-06 21:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0123_remove_role_users_role_members'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='role',
            name='unique_role_name',
        ),
    ]