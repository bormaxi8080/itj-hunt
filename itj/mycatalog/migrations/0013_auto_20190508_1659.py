# Generated by Django 2.1.7 on 2019-05-08 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0012_auto_20190429_2223'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='parced_source_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='position',
            name='source',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='position',
            name='source_url',
            field=models.URLField(blank=True),
        ),
    ]
