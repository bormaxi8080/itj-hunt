# Generated by Django 2.1.7 on 2019-07-20 20:08

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0035_auto_20190719_2316'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyPositionUrlIgnore',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_url', models.URLField()),
                ('position_name', models.CharField(blank=True, max_length=250, null=True)),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('company_name_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mycatalog.Company')),
            ],
        ),
        migrations.AlterField(
            model_name='position',
            name='pub_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date created'),
        ),
    ]