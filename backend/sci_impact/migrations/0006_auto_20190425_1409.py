# Generated by Django 2.1.7 on 2019-04-25 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0005_auto_20190424_1704'),
    ]

    operations = [
        migrations.AddField(
            model_name='venue',
            name='day',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='venue',
            name='month',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='venue',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
