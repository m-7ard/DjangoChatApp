# Generated by Django 4.0.4 on 2023-07-23 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0073_alter_groupchannel_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='content',
            field=models.CharField(default='', max_length=1024),
            preserve_default=False,
        ),
    ]
