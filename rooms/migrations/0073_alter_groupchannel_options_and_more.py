# Generated by Django 4.0.4 on 2023-07-20 14:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0072_groupchannel_description'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='groupchannel',
            options={},
        ),
        migrations.RemoveField(
            model_name='category',
            name='relative_order',
        ),
        migrations.RemoveField(
            model_name='groupchannel',
            name='relative_order',
        ),
    ]