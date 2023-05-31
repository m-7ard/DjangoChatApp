# Generated by Django 4.0.4 on 2023-05-30 10:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0007_rename_target_reaction_target_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emote',
            name='room',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='emotes', to='rooms.room'),
        ),
    ]
