# Generated by Django 2.1.7 on 2019-04-27 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyword',
            name='keyword',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
