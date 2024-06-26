# Generated by Django 4.2.5 on 2024-04-23 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('album_app', '0004_rename_album_completedlist_albums_todolist_albums'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='primary_artist',
            field=models.CharField(default='Placeholder', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='song',
            name='duration_min',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='song',
            name='duration_sec',
            field=models.IntegerField(),
        ),
    ]
