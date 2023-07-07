# Generated by Django 4.0.4 on 2023-07-05 19:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0043_backloggroup_remove_log_room_remove_message_channel_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrivateChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('backlogs', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='private_chat', to='rooms.backloggroup')),
                ('users', models.ManyToManyField(related_name='private_chats', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
