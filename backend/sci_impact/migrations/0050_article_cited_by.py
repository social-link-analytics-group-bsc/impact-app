# Generated by Django 2.2.6 on 2019-10-25 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0049_auto_20191025_1446'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='cited_by',
            field=models.IntegerField(default=0),
        ),
    ]
