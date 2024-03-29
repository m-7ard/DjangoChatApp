# Generated by Django 4.0.4 on 2023-09-03 14:52

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0093_mention'),
    ]

    operations = [
        migrations.AddField(
            model_name='backlog',
            name='mentions',
            field=models.ManyToManyField(related_name='mentioned_in', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Mention',
        ),
    ]
