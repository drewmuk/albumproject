# Generated by Django 4.2.5 on 2024-04-25 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('album_app', '0008_input_album_omit_album_delete_inputalbum_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Last_Update',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('update_date', models.DateField(null=True)),
            ],
        ),
    ]
