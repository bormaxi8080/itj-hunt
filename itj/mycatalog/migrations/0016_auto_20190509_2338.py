# Generated by Django 2.1.7 on 2019-05-09 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0015_auto_20190509_2200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='position',
            name='keyword_ref',
            field=models.ManyToManyField(blank=True, to='mycatalog.Keyword', verbose_name='Keywords'),
        ),
    ]
