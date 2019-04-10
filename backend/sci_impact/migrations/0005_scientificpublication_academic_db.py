# Generated by Django 2.1.7 on 2019-04-03 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0004_scientificpublication_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='scientificpublication',
            name='academic_db',
            field=models.CharField(choices=[('gscholar', 'Google Scholar'), ('wos', 'Web of Science'), ('scopus', 'Scopus'), ('pubmed', 'PubMed'), ('other', 'Other')], default='other', max_length=100),
        ),
    ]