# Generated by Django 4.0.4 on 2023-05-08 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='last_ping',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]