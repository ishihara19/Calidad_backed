# Generated by Django 5.2 on 2025-05-18 15:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('normas', '0005_calificacionsubcaracteristica_codigo_evaluacion'),
    ]

    operations = [
        migrations.RenameField(
            model_name='calificacionsubcaracteristica',
            old_name='codigo_evaluacion',
            new_name='codigo_calificacion',
        ),
    ]
