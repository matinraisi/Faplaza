# Generated by Django 4.2.7 on 2024-07-30 11:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price', '0008_alter_address_city_alter_address_postalcode_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='product_count',
            field=models.IntegerField(default=1),
        ),
    ]
