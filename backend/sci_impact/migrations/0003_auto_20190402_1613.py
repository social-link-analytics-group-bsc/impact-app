# Generated by Django 2.1.7 on 2019-04-02 14:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0002_auto_20190401_1727'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScientificAuthorship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_author', models.BooleanField(default=False)),
                ('corresponding_author', models.BooleanField(default=False)),
                ('institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Institution')),
            ],
        ),
        migrations.AlterModelOptions(
            name='city',
            options={'verbose_name_plural': 'cities'},
        ),
        migrations.AlterModelOptions(
            name='country',
            options={'verbose_name_plural': 'countries'},
        ),
        migrations.RenameField(
            model_name='affiliation',
            old_name='data_joined',
            new_name='date_joined',
        ),
        migrations.RenameField(
            model_name='citation',
            old_name='cite_url',
            new_name='url',
        ),
        migrations.RenameField(
            model_name='scientist',
            old_name='country',
            new_name='nationality',
        ),
        migrations.RemoveField(
            model_name='scientist',
            name='scientific_publications',
        ),
        migrations.AddField(
            model_name='affiliation',
            name='book_citations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='books',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='dataset_citations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='datasets',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='date_left',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='patent_citations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='patents',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='scientific_publications',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='scientific_publications_as_first_author',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='scientific_publications_with_citations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='tools',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='tools_citations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='affiliation',
            name='total_citations',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='citation',
            name='title',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.RemoveField(
            model_name='scientificpublication',
            name='authors'
        ),
        migrations.AddField(
            model_name='scientificpublication',
            name='authors',
            field=models.ManyToManyField(related_name='scientific_publications',
                                         through='sci_impact.ScientificAuthorship', to='sci_impact.Scientist'),
        ),
        migrations.AddField(
            model_name='scientificauthorship',
            name='scientific_publication',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sci_impact.ScientificPublication'),
        ),
        migrations.AddField(
            model_name='scientificauthorship',
            name='scientist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Scientist'),
        ),
    ]