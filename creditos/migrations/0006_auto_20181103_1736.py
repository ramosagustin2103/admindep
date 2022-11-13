# Generated by Django 2.0.7 on 2018-11-03 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('creditos', '0005_auto_20181103_1143'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mail',
            name='liquidacion',
        ),
        migrations.RemoveField(
            model_name='mail',
            name='socio',
        ),
        migrations.AddField(
            model_name='liquidacion',
            name='pdf',
            field=models.FileField(blank=True, null=True, upload_to='liquidaciones/pdf/'),
        ),
        migrations.DeleteModel(
            name='Mail',
        ),
    ]
