# Generated by Django 2.2.6 on 2019-11-25 11:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_impact', '0014_auto_20191125_1224'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialimpactsearch',
            name='executed',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]