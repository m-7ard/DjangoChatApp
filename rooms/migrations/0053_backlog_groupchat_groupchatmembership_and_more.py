# Generated by Django 4.0.4 on 2023-07-11 19:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0052_remove_channel_group_remove_room_channels_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Backlog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('message', 'Message'), ('log', 'Log')], max_length=20)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='rooms.backloggroup')),
            ],
        ),
        migrations.CreateModel(
            name='GroupChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('image', models.ImageField(default='blank.png', max_length=500, upload_to='')),
                ('public', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='groups_owned', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupChatMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('nickname', models.CharField(blank=True, max_length=20)),
                ('chat', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group', to='rooms.groupchat')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MembershipGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateChatMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='channelcategory',
            name='room',
        ),
        migrations.RemoveField(
            model_name='channelconfiguration',
            name='channel',
        ),
        migrations.RemoveField(
            model_name='channelconfiguration',
            name='role',
        ),
        migrations.RemoveField(
            model_name='channelconfigurationpermissions',
            name='config',
        ),
        migrations.RemoveField(
            model_name='chatter',
            name='group',
        ),
        migrations.RemoveField(
            model_name='chatter',
            name='user',
        ),
        migrations.RemoveField(
            model_name='chatterprofile',
            name='chatter',
        ),
        migrations.RemoveField(
            model_name='chatterprofile',
            name='roles',
        ),
        migrations.RemoveField(
            model_name='emote',
            name='room',
        ),
        migrations.RemoveField(
            model_name='reaction',
            name='chatter',
        ),
        migrations.RemoveField(
            model_name='reaction',
            name='emote',
        ),
        migrations.RemoveField(
            model_name='reaction',
            name='group',
        ),
        migrations.RemoveField(
            model_name='rolepermissions',
            name='role',
        ),
        migrations.RemoveField(
            model_name='room',
            name='chatters',
        ),
        migrations.RemoveField(
            model_name='room',
            name='default_role',
        ),
        migrations.RemoveField(
            model_name='room',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='room',
            name='roles',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='category',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='description',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='kind',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='name',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='order',
        ),
        migrations.RemoveField(
            model_name='channel',
            name='room',
        ),
        migrations.RemoveField(
            model_name='log',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='log',
            name='group',
        ),
        migrations.RemoveField(
            model_name='log',
            name='reactions',
        ),
        migrations.RemoveField(
            model_name='message',
            name='content',
        ),
        migrations.RemoveField(
            model_name='message',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='message',
            name='group',
        ),
        migrations.RemoveField(
            model_name='message',
            name='reactions',
        ),
        migrations.RemoveField(
            model_name='privatechat',
            name='chatters',
        ),
        migrations.RemoveField(
            model_name='role',
            name='admin',
        ),
        migrations.RemoveField(
            model_name='role',
            name='color',
        ),
        migrations.RemoveField(
            model_name='role',
            name='hierarchy',
        ),
        migrations.AddField(
            model_name='channel',
            name='pinned_messages',
            field=models.ManyToManyField(to='rooms.message'),
        ),
        migrations.AddField(
            model_name='privatechat',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='channel',
            name='backlogs',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='rooms.backloggroup'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='log',
            name='action',
            field=models.CharField(choices=[('join', 'joined the chat'), ('leave', 'left the chat')], default=None, max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='privatechat',
            name='backlogs',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='rooms.backloggroup'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(max_length=20),
        ),
        migrations.DeleteModel(
            name='Action',
        ),
        migrations.DeleteModel(
            name='ChannelCategory',
        ),
        migrations.DeleteModel(
            name='ChannelConfiguration',
        ),
        migrations.DeleteModel(
            name='ChannelConfigurationPermissions',
        ),
        migrations.DeleteModel(
            name='Chatter',
        ),
        migrations.DeleteModel(
            name='ChatterGroup',
        ),
        migrations.DeleteModel(
            name='ChatterProfile',
        ),
        migrations.DeleteModel(
            name='Emote',
        ),
        migrations.DeleteModel(
            name='Reaction',
        ),
        migrations.DeleteModel(
            name='ReactionGroup',
        ),
        migrations.DeleteModel(
            name='RoleGroup',
        ),
        migrations.DeleteModel(
            name='RolePermissions',
        ),
        migrations.DeleteModel(
            name='Room',
        ),
        migrations.AddField(
            model_name='privatechatmembership',
            name='chat',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='private', to='rooms.privatechat'),
        ),
        migrations.AddField(
            model_name='privatechatmembership',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group_chat_memberships', to='rooms.membershipgroup'),
        ),
        migrations.AddField(
            model_name='groupchatmembership',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='private_chat_memberships', to='rooms.membershipgroup'),
        ),
        migrations.AddField(
            model_name='channel',
            name='chat',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='rooms.groupchat'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='log',
            name='backlog',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='log', to='rooms.backlog'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='message',
            name='backlog',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='message', to='rooms.backlog'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='role',
            name='chat',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='rooms.groupchat'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='role',
            name='memberships',
            field=models.ManyToManyField(related_name='roles', to='rooms.groupchatmembership'),
        ),
    ]