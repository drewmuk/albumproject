# Generated by Django 4.2.5 on 2023-09-19 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('album_app', '0002_todolist_completedlist'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='completedlist',
            name='albums',
        ),
        migrations.RemoveField(
            model_name='todolist',
            name='albums',
        ),
        migrations.AddField(
            model_name='completedlist',
            name='album',
            field=models.ManyToManyField(related_name='completed_list_albums', to='album_app.album'),
        ),
    ]
