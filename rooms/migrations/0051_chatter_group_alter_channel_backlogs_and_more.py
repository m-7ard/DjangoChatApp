# Generated by Django 4.0.4 on 2023-07-08 11:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rooms', '0050_channelgroup_chatter_chattergroup_chatterprofile_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatter',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chatters', to='rooms.chattergroup'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='backlogs',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='channel', to='rooms.backloggroup'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='channels', to='rooms.channelgroup'),
        ),
        migrations.AlterField(
            model_name='channelcategory',
            name='room',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='rooms.room'),
        ),
        migrations.AlterField(
            model_name='message',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='reaction',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='rooms.reactiongroup'),
        ),
    ]