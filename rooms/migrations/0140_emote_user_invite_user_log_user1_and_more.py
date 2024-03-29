# Generated by Django 4.2.6 on 2023-10-19 22:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0023_alter_userarchive_user'),
        ('rooms', '0139_message_user_alter_message_user_archive'),
    ]

    operations = [
        migrations.AddField(
            model_name='emote',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invite',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='log',
            name='user1',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='emote',
            name='user_archive',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.userarchive'),
        ),
        migrations.AlterField(
            model_name='invite',
            name='user_archive',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='users.userarchive'),
        ),
        migrations.AlterField(
            model_name='log',
            name='user1_archive',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='users.userarchive'),
        ),
        migrations.AlterField(
            model_name='log',
            name='user2_archive',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='users.userarchive'),
        ),
    ]
