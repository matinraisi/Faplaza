# Generated by Django 4.2.7 on 2024-07-28 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrape', '0002_scrapedata_price_scrapedata_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapedata',
            name='url',
            field=models.URLField(unique=True),
        ),
    ]