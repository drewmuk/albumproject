# Generated by Django 4.2.5 on 2024-04-26 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('album_app', '0009_last_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='last_update',
            name='update_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]