# Generated by Django 4.0.4 on 2023-02-26 15:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0009_usertab'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usertab',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tabs', to=settings.AUTH_USER_MODEL),
        ),
    ]