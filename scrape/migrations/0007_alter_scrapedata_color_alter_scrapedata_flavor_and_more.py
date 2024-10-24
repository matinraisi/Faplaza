# Generated by Django 4.2.14 on 2024-08-17 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrape', '0006_scrapedata_available_scrapedata_images_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrapedata',
            name='color',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AlterField(
            model_name='scrapedata',
            name='flavor',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AlterField(
            model_name='scrapedata',
            name='size',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
        migrations.AlterField(
            model_name='scrapedata',
            name='style',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
