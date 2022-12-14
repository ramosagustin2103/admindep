# Generated by Django 2.0.7 on 2018-11-27 23:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reportes', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cierre',
            name='numero_aleatorio',
        ),
        migrations.RemoveField(
            model_name='cierre',
            name='reportes',
        ),
        migrations.RemoveField(
            model_name='cierre',
            name='subtotales',
        ),
        migrations.RemoveField(
            model_name='reporte',
            name='numero_aleatorio',
        ),
        migrations.RemoveField(
            model_name='subtotal',
            name='numero_aleatorio',
        ),
        migrations.AddField(
            model_name='reporte',
            name='cierre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reportes', to='reportes.Cierre'),
        ),
        migrations.AddField(
            model_name='subtotal',
            name='cierre',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subtotales', to='reportes.Cierre'),
        ),
    ]
