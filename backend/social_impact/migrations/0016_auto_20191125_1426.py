# Generated by Django 2.2.6 on 2019-11-25 13:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social_impact', '0015_socialimpactsearch_executed'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='socialimpactsearch',
            options={'verbose_name_plural': 'Social Impact Searches'},
        ),
        migrations.RenameField(
            model_name='socialimpactsearch',
            old_name='executed',
            new_name='completed',
        ),
        migrations.CreateModel(
            name='SocialImpactSearchPublication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('completed', models.BooleanField(default=False, editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_impact.Publication')),
                ('social_impact_header', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_impact.SocialImpactSearch')),
            ],
            options={
                'verbose_name_plural': 'Social Impact Details',
            },
        ),
    ]
