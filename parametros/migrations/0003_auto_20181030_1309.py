# Generated by Django 2.0.7 on 2018-10-30 16:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parametros', '0002_socio_es_socio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socio',
            name='categoria',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='socios', to='parametros.Categoria'),
        ),
    ]
