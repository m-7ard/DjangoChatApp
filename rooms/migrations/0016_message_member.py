# Generated by Django 4.0.4 on 2023-02-11 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0015_remove_message_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='member',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='rooms.member'),
        ),
    ]
