# Generated by Django 2.0.3 on 2020-05-09 22:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('op', '0002_auto_20181030_1148'),
    ]

    operations = [
        migrations.AddField(
            model_name='cajaop',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='deudaop',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gastodeuda',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='gastoop',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='retencionop',
            name='fecha',
            field=models.DateField(blank=True, null=True),
        ),
    ]
