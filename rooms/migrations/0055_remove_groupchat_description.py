# Generated by Django 4.0.4 on 2023-07-16 18:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0054_remove_membershipgroup_user_remove_backlog_group_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupchat',
            name='description',
        ),
    ]