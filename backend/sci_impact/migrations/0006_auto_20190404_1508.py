# Generated by Django 2.1.7 on 2019-04-04 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0005_scientificpublication_academic_db'),
    ]

    operations = [
        migrations.RenameField(
            model_name='affiliation',
            old_name='date_joined',
            new_name='departure_date',
        ),
        migrations.RenameField(
            model_name='affiliation',
            old_name='date_left',
            new_name='joined_date',
        ),
    ]
