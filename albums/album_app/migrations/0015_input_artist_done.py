# Generated by Django 4.2.5 on 2024-04-26 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('album_app', '0014_alter_input_artist_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='input_artist',
            name='done',
            field=models.IntegerField(default=0),
        ),
    ]
