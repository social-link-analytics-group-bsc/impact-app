# Generated by Django 2.1.7 on 2019-06-18 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0040_auto_20190618_1653'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='fieldcitations',
            options={'verbose_name_plural': 'field citations'},
        ),
        migrations.AddField(
            model_name='fieldcitations',
            name='field',
            field=models.CharField(default=' ', max_length=200),
            preserve_default=False,
        ),
    ]
