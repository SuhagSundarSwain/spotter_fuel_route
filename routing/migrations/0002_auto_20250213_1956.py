# Generated by Django 3.2.23 on 2025-02-13 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fuelstation',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='fuelstation',
            name='longitude',
            field=models.FloatField(null=True),
        ),
    ]
