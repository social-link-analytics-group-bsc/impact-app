# Generated by Django 2.2.6 on 2019-11-06 12:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0051_institution_is_inb'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='impactdetail',
            unique_together={('impact_header', 'year')},
        ),
    ]
