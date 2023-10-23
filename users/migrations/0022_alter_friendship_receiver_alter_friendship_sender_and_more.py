# Generated by Django 4.2.6 on 2023-10-18 14:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_archive_delete_news'),
        ('users', '0021_alter_friendship_receiver_alter_friendship_sender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='friendship',
            name='receiver',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='received_friendships', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='friendship',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_friendships', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userarchive',
            name='archive',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='core.archive'),
        ),
        migrations.DeleteModel(
            name='Archive',
        ),
    ]