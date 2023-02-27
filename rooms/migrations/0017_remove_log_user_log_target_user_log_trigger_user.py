# Generated by Django 4.0.4 on 2023-02-17 23:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0016_message_member'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='log',
            name='user',
        ),
        migrations.AddField(
            model_name='log',
            name='target_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_activity', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='log',
            name='trigger_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_actions', to=settings.AUTH_USER_MODEL),
        ),
    ]