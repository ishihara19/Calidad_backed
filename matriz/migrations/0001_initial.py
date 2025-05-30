# Generated by Django 5.2 on 2025-05-27 14:06

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('empresa', '0004_empresa_tamaño_empresa_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MatrizRiesgo',
            fields=[
                ('id', models.CharField(editable=False, max_length=20, primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre de la Matriz')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('responsable', models.CharField(blank=True, max_length=100, verbose_name='Responsable')),
                ('fecha_creacion', models.DateField(verbose_name='Fecha de Creación')),
                ('fecha_modificacion', models.DateTimeField(auto_now=True, verbose_name='Fecha de Modificación')),
                ('creado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Creado por')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matrices_riesgo', to='empresa.empresa', verbose_name='Empresa')),
            ],
            options={
                'verbose_name': 'Matriz de Riesgo',
                'verbose_name_plural': 'Matrices de Riesgo',
                'ordering': ['-fecha_modificacion'],
            },
        ),
        migrations.CreateModel(
            name='AuditoriaMatriz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(choices=[('CREATE', 'Creación'), ('UPDATE', 'Actualización'), ('DELETE', 'Eliminación')], max_length=10)),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción del cambio')),
                ('fecha_accion', models.DateTimeField(auto_now_add=True)),
                ('datos_anteriores', models.JSONField(blank=True, null=True, verbose_name='Datos anteriores')),
                ('datos_nuevos', models.JSONField(blank=True, null=True, verbose_name='Datos nuevos')),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auditoria', to='matriz.matrizriesgo')),
            ],
            options={
                'verbose_name': 'Auditoría de Matriz',
                'verbose_name_plural': 'Auditorías de Matrices',
                'ordering': ['-fecha_accion'],
            },
        ),
        migrations.CreateModel(
            name='ParametroMatriz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('PROBABILIDAD', 'Probabilidad'), ('IMPACTO', 'Impacto')], max_length=20, verbose_name='Tipo de Parámetro')),
                ('valor', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Valor')),
                ('etiqueta', models.CharField(max_length=50, verbose_name='Etiqueta')),
                ('descripcion', models.TextField(verbose_name='Descripción')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
            ],
            options={
                'verbose_name': 'Parámetro del Sistema',
                'verbose_name_plural': 'Parámetros del Sistema',
                'ordering': ['tipo', 'valor'],
                'unique_together': {('tipo', 'valor')},
            },
        ),
        migrations.CreateModel(
            name='RiesgoMatriz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveIntegerField(verbose_name='Número')),
                ('fecha', models.DateField(verbose_name='Fecha')),
                ('codigo', models.CharField(blank=True, max_length=50, verbose_name='Código')),
                ('nombre', models.CharField(max_length=300, verbose_name='Nombre del Riesgo')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción del Riesgo')),
                ('efectos', models.TextField(blank=True, verbose_name='Efectos/Consecuencias')),
                ('tipo_riesgo', models.CharField(blank=True, choices=[('Operativo', 'Operativo'), ('Estratégico', 'Estratégico'), ('Financiero', 'Financiero'), ('Cumplimiento', 'Cumplimiento'), ('Tecnológico', 'Tecnológico')], max_length=20, verbose_name='Tipo de Riesgo')),
                ('probabilidad', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Probabilidad')),
                ('impacto', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='Impacto')),
                ('controles_existentes', models.TextField(blank=True, verbose_name='Controles Existentes')),
                ('tipo_control', models.CharField(choices=[('Preventivo', 'Preventivo'), ('Correctivo', 'Correctivo'), ('Detectivo', 'Detectivo')], default='Preventivo', max_length=20, verbose_name='Tipo de Control')),
                ('efectividad_control', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name='Efectividad del Control (%)')),
                ('controles_evaluacion', models.JSONField(blank=True, default=dict, verbose_name='Evaluación de Controles')),
                ('tratamiento', models.TextField(blank=True, verbose_name='Tratamiento/Controles Propuestos')),
                ('responsable_control', models.CharField(blank=True, max_length=100, verbose_name='Responsable del Control')),
                ('aceptado', models.BooleanField(default=False, verbose_name='¿Se acepta el riesgo?')),
                ('matriz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='riesgos', to='matriz.matrizriesgo')),
            ],
            options={
                'verbose_name': 'Riesgo',
                'verbose_name_plural': 'Riesgos',
                'ordering': ['numero'],
                'unique_together': {('matriz', 'numero')},
            },
        ),
        migrations.CreateModel(
            name='CausaRiesgo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('causa', models.TextField(verbose_name='Descripción de la Causa')),
                ('factor', models.CharField(blank=True, choices=[('Información', 'Información'), ('Método', 'Método'), ('Personas', 'Personas'), ('Sistemas de información', 'Sistemas de información'), ('Infraestructura', 'Infraestructura')], max_length=50, verbose_name='Factor de Causa')),
                ('controles', models.TextField(blank=True, verbose_name='Controles Asociados')),
                ('orden', models.PositiveIntegerField(default=1, verbose_name='Orden')),
                ('riesgo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='causas', to='matriz.riesgomatriz')),
            ],
            options={
                'verbose_name': 'Causa del Riesgo',
                'verbose_name_plural': 'Causas del Riesgo',
                'ordering': ['orden'],
            },
        ),
    ]
