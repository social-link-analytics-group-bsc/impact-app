# Generated by Django 2.1.7 on 2019-05-27 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0033_auto_20190527_1608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artifact',
            name='url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
