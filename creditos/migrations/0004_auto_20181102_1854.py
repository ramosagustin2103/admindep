# Generated by Django 2.0.7 on 2018-11-02 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creditos', '0003_factura_observacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='pdf',
            field=models.FileField(blank=True, null=True, upload_to='facturas/pdf/'),
        ),
    ]
