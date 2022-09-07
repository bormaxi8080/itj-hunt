# Generated by Django 2.1.7 on 2019-06-30 14:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0032_position_salary_frequency'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='employment_type',
            field=models.CharField(blank=True, choices=[('FULLTIME', 'Full-time'), ('PARTTIME', 'Part-time'), ('CONTRACT', 'Contract'), ('INTERNSHIP', 'Internship'), ('ENTRYLEVEL', 'Entry level')], default='FULLTIME', max_length=30),
        ),
    ]