# Generated by Django 2.1.7 on 2019-04-03 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0003_auto_20190402_1613'),
    ]

    operations = [
        migrations.AddField(
            model_name='scientificpublication',
            name='source',
            field=models.CharField(default='', max_length=100),
        ),
    ]