# Generated by Django 4.0.4 on 2023-07-19 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0070_alter_category_relative_order_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupchannel',
            name='pinned_messages',
            field=models.ManyToManyField(blank=True, to='rooms.message'),
        ),
        migrations.AlterField(
            model_name='privatechannel',
            name='pinned_messages',
            field=models.ManyToManyField(blank=True, to='rooms.message'),
        ),
    ]