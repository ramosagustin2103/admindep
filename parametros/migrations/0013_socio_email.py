# Generated by Django 2.0.7 on 2018-12-31 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parametros', '0012_categoria_baja'),
    ]

    operations = [
        migrations.AddField(
            model_name='socio',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
