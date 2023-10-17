# Generated by Django 4.2.6 on 2023-10-17 11:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_rename_userwrapper_userarchive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userarchive',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='archive_wrapper', to=settings.AUTH_USER_MODEL),
        ),
    ]
