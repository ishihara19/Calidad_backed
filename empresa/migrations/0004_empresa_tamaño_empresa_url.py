# Generated by Django 5.2 on 2025-05-27 03:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('empresa', '0003_alter_empresa_codigo_empresa'),
    ]

    operations = [
        migrations.AddField(
            model_name='empresa',
            name='tamaño',
            field=models.CharField(choices=[('Pequeña', 'Empresa Pequeña'), ('Mediana', 'Empresa Mediana'), ('Grande', 'Empresa Grande')], default='Mediana', max_length=50),
        ),
        migrations.AddField(
            model_name='empresa',
            name='url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
