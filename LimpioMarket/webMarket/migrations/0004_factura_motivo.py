# Generated by Django 5.0.6 on 2024-07-02 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webMarket', '0003_detalleestado'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='motivo',
            field=models.TextField(blank=True, null=True),
        ),
    ]