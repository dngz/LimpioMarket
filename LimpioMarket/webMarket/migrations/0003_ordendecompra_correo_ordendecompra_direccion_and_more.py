# Generated by Django 5.0.4 on 2024-05-30 03:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webMarket', '0002_alter_ordendecompra_productos'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordendecompra',
            name='correo',
            field=models.EmailField(default='', max_length=254),
        ),
        migrations.AddField(
            model_name='ordendecompra',
            name='direccion',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='ordendecompra',
            name='rut',
            field=models.CharField(default='', max_length=10),
        ),
    ]