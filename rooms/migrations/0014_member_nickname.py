# Generated by Django 4.0.4 on 2023-02-10 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0013_rename_member_user_message_user_alter_message_member'),
    ]

    operations = [
        migrations.AddField(
            model_name='member',
            name='nickname',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
