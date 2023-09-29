# Generated by Django 4.0.4 on 2023-09-29 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0115_role_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='kind',
        ),
        migrations.AddField(
            model_name='role',
            name='admin',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='can_ban_members',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_create_invites',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='can_create_messages',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='can_get_invites',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='can_kick_members',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_manage_channels',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_manage_chat',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_manage_emotes',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_manage_invites',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_manage_messages',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_manage_roles',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='role',
            name='can_mention_all',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='can_react',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='role',
            name='can_see_channels',
            field=models.ManyToManyField(related_name='can_see_channel', to='rooms.groupchannel'),
        ),
        migrations.AddField(
            model_name='role',
            name='can_use_channels',
            field=models.ManyToManyField(related_name='can_use_channel', to='rooms.groupchannel'),
        ),
    ]