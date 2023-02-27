# Generated by Django 4.0.4 on 2023-02-10 13:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0010_log_action_display_name_remove_log_action_log_action'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='user',
        ),
        migrations.AddField(
            model_name='message',
            name='member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='rooms.member'),
        ),
        migrations.AddField(
            model_name='message',
            name='member_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to=settings.AUTH_USER_MODEL),
        ),
    ]
