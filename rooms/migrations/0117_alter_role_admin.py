# Generated by Django 4.0.4 on 2023-09-30 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0116_remove_role_kind_role_admin_role_can_ban_members_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='admin',
            field=models.BooleanField(default=False),
        ),
    ]
