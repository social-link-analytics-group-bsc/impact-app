# Generated by Django 2.1.7 on 2019-06-18 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0043_auto_20190618_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='impact',
            name='total_weighted_impact',
            field=models.FloatField(default=0),
        ),
    ]
