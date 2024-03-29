# Generated by Django 4.0.4 on 2023-06-16 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('rooms', '0029_alter_channelconfiguration_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='role',
            options={'permissions': [('manage_role', 'Can manage role'), ('mention_all', 'Can mention @all')]},
        ),
        migrations.AlterModelOptions(
            name='room',
            options={'permissions': [('kick_user', 'Can kick user'), ('ban_user', 'Can ban user'), ('read_logs', 'Can read logs')]},
        ),
        migrations.AddField(
            model_name='role',
            name='admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='role',
            name='permissions',
            field=models.ManyToManyField(limit_choices_to={'codename__in': ['add_message', 'delete_message', 'view_message', 'view_channel', 'add_reaction', 'attach_image', 'change_nickname', 'manage_nickname', 'manage_channel', 'manage_role', 'change_room', 'mention_all', 'pin_message', 'kick_user', 'ban_user', 'read_logs']}, to='auth.permission'),
        ),
    ]
