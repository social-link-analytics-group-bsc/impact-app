# Generated by Django 2.1.7 on 2019-04-01 15:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Country'),
        ),
        migrations.AddField(
            model_name='institution',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Region'),
        ),
    ]
