# Generated by Django 4.0.4 on 2023-02-21 23:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0019_messagereaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='unique_reactions',
            field=models.ManyToManyField(to='rooms.reaction'),
        ),
    ]