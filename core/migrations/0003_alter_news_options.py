# Generated by Django 4.0.4 on 2023-01-27 20:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_news_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='news',
            options={'verbose_name_plural': 'News'},
        ),
    ]
