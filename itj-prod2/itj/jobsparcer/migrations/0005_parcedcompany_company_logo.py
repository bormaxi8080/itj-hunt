# Generated by Django 2.1.7 on 2019-05-08 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobsparcer', '0004_auto_20190508_1822'),
    ]

    operations = [
        migrations.AddField(
            model_name='parcedcompany',
            name='company_logo',
            field=models.ImageField(blank=True, max_length=2000, null=True, upload_to='logos'),
        ),
    ]