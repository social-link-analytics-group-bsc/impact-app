# Generated by Django 2.1.7 on 2019-05-30 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0035_auto_20190528_1046'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='inb_pi_as_author',
            field=models.BooleanField(default=False),
        ),
    ]
