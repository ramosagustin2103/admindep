# Generated by Django 2.0.7 on 2018-10-30 14:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contabilidad', '0001_initial'),
        ('afip', '0003_auto_20180821_1213'),
        ('creditos', '0001_initial'),
        ('parametros', '0001_initial'),
        ('clubes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mail',
            name='socio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parametros.Socio'),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='asiento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contabilidad.Asiento'),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='club',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clubes.Club'),
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='punto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='afip.PointOfSales'),
        ),
        migrations.AddField(
            model_name='factura',
            name='club',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clubes.Club'),
        ),
        migrations.AddField(
            model_name='factura',
            name='liquidacion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='creditos.Liquidacion'),
        ),
        migrations.AddField(
            model_name='factura',
            name='receipt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='afip.Receipt'),
        ),
        migrations.AddField(
            model_name='factura',
            name='socio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parametros.Socio'),
        ),
        migrations.AddField(
            model_name='credito',
            name='accesorios',
            field=models.ManyToManyField(blank=True, to='parametros.Accesorio'),
        ),
        migrations.AddField(
            model_name='credito',
            name='club',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clubes.Club'),
        ),
        migrations.AddField(
            model_name='credito',
            name='factura',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='creditos.Factura'),
        ),
        migrations.AddField(
            model_name='credito',
            name='ingreso',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parametros.Ingreso'),
        ),
        migrations.AddField(
            model_name='credito',
            name='liquidacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='creditos.Liquidacion'),
        ),
        migrations.AddField(
            model_name='credito',
            name='padre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hijos', to='creditos.Credito'),
        ),
        migrations.AddField(
            model_name='credito',
            name='socio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parametros.Socio'),
        ),
    ]
