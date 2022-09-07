# Generated by Django 2.1.7 on 2019-05-26 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0022_companydomainsclassifier_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='archive_flag',
            field=models.BooleanField(default=False, verbose_name='Archived'),
        ),
        migrations.AddField(
            model_name='position',
            name='edited_date',
            field=models.DateTimeField(auto_now=True, verbose_name='Date edited'),
        ),
    ]
