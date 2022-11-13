# Generated by Django 2.0.7 on 2018-10-30 14:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('mp', '0018_auto_20180808_1242'),
        ('contabilidad', '0001_initial'),
        ('comprobantes', '0001_initial'),
        ('parametros', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('creditos', '0001_initial'),
        ('clubes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='saldo',
            name='socio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='parametros.Socio'),
        ),
        migrations.AddField(
            model_name='comprobante',
            name='asiento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contabilidad.Asiento'),
        ),
        migrations.AddField(
            model_name='comprobante',
            name='club',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clubes.Club'),
        ),
        migrations.AddField(
            model_name='comprobante',
            name='socio',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parametros.Socio'),
        ),
        migrations.AddField(
            model_name='comprobante',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cobro',
            name='club',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clubes.Club'),
        ),
        migrations.AddField(
            model_name='cobro',
            name='comprobante',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='comprobantes.Comprobante'),
        ),
        migrations.AddField(
            model_name='cobro',
            name='credito',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='creditos.Credito'),
        ),
        migrations.AddField(
            model_name='cobro',
            name='mercado_pago',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='mp.Payment'),
        ),
        migrations.AddField(
            model_name='cobro',
            name='socio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='parametros.Socio'),
        ),
        migrations.AddField(
            model_name='cajacomprobante',
            name='caja',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='parametros.Caja'),
        ),
        migrations.AddField(
            model_name='cajacomprobante',
            name='comprobante',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='comprobantes.Comprobante'),
        ),
    ]