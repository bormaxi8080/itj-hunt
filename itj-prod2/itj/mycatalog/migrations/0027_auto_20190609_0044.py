# Generated by Django 2.1.7 on 2019-06-08 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mycatalog', '0026_position_position_id_redirect_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='count_apply',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='position',
            name='count_view',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
