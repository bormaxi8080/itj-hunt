# Generated by Django 2.1.7 on 2019-05-09 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0013_auto_20190508_1659'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='parced_source_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='keyword',
            name='parced_source_id',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]