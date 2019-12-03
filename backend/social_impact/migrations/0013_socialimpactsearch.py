# Generated by Django 2.2.6 on 2019-11-25 11:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('social_impact', '0012_auto_20191122_1649'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialImpactSearch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('dictionary', models.FileField(blank=True, max_length=500, null=True, upload_to='dictionaries/')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('publications', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='social_impact.Publication')),
            ],
        ),
    ]