# Generated by Django 2.2.6 on 2019-11-21 15:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social_impact', '0003_auto_20191121_1229'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='budget_contribution_eu',
            new_name='budget_eu',
        ),
    ]
