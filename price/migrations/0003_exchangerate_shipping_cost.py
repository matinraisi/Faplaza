# Generated by Django 5.0.6 on 2024-07-08 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price', '0002_exchangerate_delete_power'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangerate',
            name='shipping_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
