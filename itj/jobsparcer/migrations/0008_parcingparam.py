# Generated by Django 2.1.7 on 2019-06-01 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobsparcer', '0007_auto_20190531_2316'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParcingParam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('value', models.CharField(blank=True, max_length=100)),
            ],
        ),
    ]
