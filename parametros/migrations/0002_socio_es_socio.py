# Generated by Django 2.0.7 on 2018-10-30 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parametros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='socio',
            name='es_socio',
            field=models.BooleanField(default=True),
        ),
    ]
