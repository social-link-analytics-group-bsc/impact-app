# Generated by Django 2.2.6 on 2019-11-21 15:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('social_impact', '0004_auto_20191121_1614'),
    ]

    operations = [
        migrations.RenameField(
            model_name='project',
            old_name='coordinated_by',
            new_name='coordinator',
        ),
    ]