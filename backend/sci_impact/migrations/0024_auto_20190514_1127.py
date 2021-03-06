# Generated by Django 2.1.7 on 2019-05-14 09:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sci_impact', '0023_auto_20190514_1101'),
    ]

    operations = [
        migrations.CreateModel(
            name='NetworkEdge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attrs', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.CustomField')),
            ],
        ),
        migrations.CreateModel(
            name='NetworkNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('attrs', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sci_impact.CustomField')),
            ],
        ),
        migrations.RemoveField(
            model_name='network',
            name='num_edges',
        ),
        migrations.RemoveField(
            model_name='network',
            name='num_nodes',
        ),
        migrations.AddField(
            model_name='networknode',
            name='network',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sci_impact.Network'),
        ),
        migrations.AddField(
            model_name='networkedge',
            name='node_a',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='node_a', to='sci_impact.NetworkNode'),
        ),
        migrations.AddField(
            model_name='networkedge',
            name='node_b',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='node_b', to='sci_impact.NetworkNode'),
        ),
    ]
