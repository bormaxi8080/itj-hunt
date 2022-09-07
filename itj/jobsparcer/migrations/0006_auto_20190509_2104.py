# Generated by Django 2.1.7 on 2019-05-09 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobsparcer', '0005_parcedcompany_company_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='parcedcompany',
            name='catalog_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='parcedposition',
            name='catalog_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='parcedtag',
            name='catalog_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
