# Generated by Django 4.0.4 on 2023-03-13 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0031_remove_channelcategory_one_base_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='channels', to='rooms.channelcategory'),
        ),
    ]
