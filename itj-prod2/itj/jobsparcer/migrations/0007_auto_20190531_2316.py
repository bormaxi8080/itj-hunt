# Generated by Django 2.1.7 on 2019-05-31 20:16

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobsparcer', '0006_auto_20190509_2104'),
    ]

    operations = [
        migrations.AddField(
            model_name='parcedcompany',
            name='company_pitch',
            field=ckeditor.fields.RichTextField(blank=True),
        ),
        migrations.AddField(
            model_name='parcedcompany',
            name='description',
            field=ckeditor.fields.RichTextField(blank=True),
        ),
        migrations.AddField(
            model_name='parcedcompany',
            name='offices_locations',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='parcedcompany',
            name='source',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='parcedcompany',
            name='website',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='parcedposition',
            name='source',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
