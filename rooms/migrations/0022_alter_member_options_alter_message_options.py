# Generated by Django 4.0.4 on 2023-06-13 17:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0021_alter_member_options_alter_message_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='member',
            options={'permissions': [('change_nickname', 'Can change nickname'), ('manage_nickname', 'Can manage nickname')]},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ('date_added',), 'permissions': [('pin_message', 'Can pin message'), ('attach_image', 'Can attach image')]},
        ),
    ]
