# Generated by Django 4.2.6 on 2023-10-19 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0135_rename_user_privatechatmembership_user_archive'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatechat',
            name='kind',
            field=models.CharField(choices=[('direct', 'direct private chat'), ('group', 'group private chat')], default='direct', max_length=20),
        ),
    ]
