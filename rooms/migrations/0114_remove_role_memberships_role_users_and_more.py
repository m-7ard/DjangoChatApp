# Generated by Django 4.0.4 on 2023-09-27 21:44

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0113_rename_mentions_backlog_user_mentions_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='role',
            name='memberships',
        ),
        migrations.AddField(
            model_name='role',
            name='users',
            field=models.ManyToManyField(related_name='roles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='role',
            constraint=models.UniqueConstraint(fields=('name', 'chat'), name='unique_role_name'),
        ),
    ]