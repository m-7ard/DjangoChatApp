# Generated by Django 4.0.4 on 2023-02-09 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooms', '0006_alter_log_room_alter_log_user_alter_member_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('description', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='role',
            name='color',
            field=models.CharField(default='#e0dbd1', max_length=7),
        ),
        migrations.RemoveField(
            model_name='log',
            name='action',
        ),
        migrations.AddField(
            model_name='log',
            name='action',
            field=models.ManyToManyField(related_name='logs', to='rooms.action'),
        ),
    ]