# Generated by Django 2.1.7 on 2019-06-20 15:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0045_auto_20190619_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='impact',
            name='institution',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Institution'),
        ),
        migrations.AddField(
            model_name='impact',
            name='scientist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Scientist'),
        ),
    ]