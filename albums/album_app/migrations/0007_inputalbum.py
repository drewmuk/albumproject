# Generated by Django 4.2.5 on 2024-04-24 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('album_app', '0006_input_artist'),
    ]

    operations = [
        migrations.CreateModel(
            name='InputAlbum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('by_name', models.CharField(max_length=255)),
                ('album_id', models.CharField(max_length=255)),
            ],
        ),
    ]
