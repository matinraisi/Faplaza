# Generated by Django 4.2.14 on 2024-08-18 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price', '0010_product_created_at_product_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='status',
            field=models.CharField(choices=[('Processing', 'Processing'), ('Confirmed', 'Confirmed'), ('Failed', 'Failed')], default='Processing', max_length=50),
        ),
    ]