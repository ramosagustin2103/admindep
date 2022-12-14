# Generated by Django 2.0.7 on 2018-12-29 14:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('parametros', '0012_categoria_baja'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bienvenida',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mail', models.EmailField(max_length=254)),
                ('saludo', models.TextField(blank=True, null=True)),
                ('fecha_envio', models.DateField(blank=True, null=True)),
                ('socio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parametros.Socio')),
            ],
        ),
    ]
