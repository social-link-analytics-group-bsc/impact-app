# Generated by Django 2.1.7 on 2019-04-26 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0011_auto_20190426_1104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venue',
            name='issue',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]