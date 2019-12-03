# Generated by Django 2.2.6 on 2019-12-03 13:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('social_impact', '0020_auto_20191126_1610'),
    ]

    operations = [
        migrations.RenameField(
            model_name='siormeasurement',
            old_name='description_improvement',
            new_name='description_achievement',
        ),
        migrations.AlterField(
            model_name='siormeasurement',
            name='sdg',
            field=models.CharField(choices=[('poverty', 'No poverty (SDG #1)'), ('hunger', 'Zero hunger (SDG #2)'), ('health', 'Good health and well-being (SGD #3)'), ('education', 'Quality education (SGD #4)'), ('gender', 'Gender equality (SGD #5)'), ('water', 'Clean water and sanitation (SGD #6)'), ('energy', 'Affordable and clean energy (SGD #7)'), ('work', 'Decent work and economic growth (SGD #8)'), ('industry', 'Industry, innovation, and infrastructure (SGD #9)'), ('inequalities', 'Reduced inequalities (SGD #10)'), ('sustainable', 'Sustainable cities and communities (SGD #11)'), ('consumption', 'Responsible consumption and production (SGD #12)'), ('climate', 'Climate action (SGD #13)'), ('life_water', 'Life below water (SGD #14)'), ('life_land', 'Life on land (SGD #15)'), ('peace', 'Peace, justice, and strong institutions (SGD #16)'), ('partnership', 'Partnership for the goals (SGD #17)'), ('other', 'Other societal objectives')], max_length=300, verbose_name='Social Target'),
        ),
    ]
