# Generated by Django 2.1.7 on 2019-04-29 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0010_auto_20190429_2035'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='companydomainsclassifier',
            options={'verbose_name': 'Company Domain', 'verbose_name_plural': 'Company Domains'},
        ),
        migrations.RemoveField(
            model_name='position',
            name='keywords',
        ),
        migrations.AddField(
            model_name='position',
            name='keyword_ref',
            field=models.ManyToManyField(to='mycatalog.Keyword'),
        ),
    ]
