# Generated by Django 2.1.7 on 2019-04-23 14:58

import ckeditor.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_name', models.CharField(max_length=250)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=250)),
                ('company_logo', models.ImageField(blank=True, max_length=2000, null=True, upload_to='logos')),
                ('company_email', models.EmailField(blank=True, max_length=250, null=True)),
                ('description', ckeditor.fields.RichTextField(blank=True)),
                ('offices_locations', models.CharField(max_length=250)),
                ('enabled_flag', models.BooleanField(default=False, verbose_name='Published')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('slug', models.SlugField(blank=True)),
                ('positions_url', models.URLField(blank=True)),
            ],
            options={
                'verbose_name': 'Company',
                'verbose_name_plural': 'Companies',
            },
        ),
        migrations.CreateModel(
            name='CompanyBenefit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('benefit_name', models.CharField(max_length=250)),
                ('company_name_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mycatalog.Company')),
            ],
        ),
        migrations.CreateModel(
            name='CompanyUrl',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url_text', models.URLField(max_length=250)),
                ('url_type', models.CharField(choices=[('MAIN', 'MAIN'), ('LINKEDIN', 'LINKEDIN'), ('ANGELCO', 'ANGELCO'), ('CRUNCHBASE', 'CRUNCHBASE'), ('FACEBOOK', 'FACEBOOK'), ('TWITTER', 'TWITTER'), ('OTHER', 'OTHER')], default='OTHER', max_length=10)),
                ('company_name_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mycatalog.Company')),
            ],
        ),
        migrations.CreateModel(
            name='Keyword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=100)),
                ('slug', models.SlugField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_name', models.CharField(max_length=250)),
                ('job_description', ckeditor.fields.RichTextField(verbose_name='Job Description')),
                ('responsibilities', ckeditor.fields.RichTextField(blank=True)),
                ('requirements', ckeditor.fields.RichTextField(blank=True)),
                ('salary_from', models.PositiveIntegerField(blank=True, null=True)),
                ('salary_to', models.PositiveIntegerField(blank=True, null=True)),
                ('salary_currency', models.CharField(blank=True, choices=[('USD', 'USD'), ('EUR', 'EUR'), ('GBP', 'GBP')], default='USD', max_length=10)),
                ('how_to_apply', ckeditor.fields.RichTextField(blank=True)),
                ('apply_url', models.URLField(blank=True)),
                ('apply_email', models.EmailField(blank=True, max_length=250)),
                ('locations', models.CharField(blank=True, max_length=250)),
                ('language', models.CharField(blank=True, max_length=250)),
                ('enabled_flag', models.BooleanField(default=False, verbose_name='Published')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('slug', models.SlugField(blank=True)),
                ('category_name_ref', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mycatalog.Category', verbose_name='Category')),
                ('company_name_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mycatalog.Company', verbose_name='Company')),
            ],
        ),
        migrations.CreateModel(
            name='PositionKeyword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mycatalog.Keyword', verbose_name='Keyword')),
                ('position_name_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mycatalog.Position')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='positionkeyword',
            unique_together={('position_name_ref', 'keyword_ref')},
        ),
    ]
