# Generated by Django 2.1.7 on 2019-06-18 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0041_auto_20190618_1658'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fieldcitations',
            old_name='source',
            new_name='source_name',
        ),
        migrations.AddField(
            model_name='fieldcitations',
            name='source_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
