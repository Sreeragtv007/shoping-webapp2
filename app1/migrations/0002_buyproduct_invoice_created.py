# Generated by Django 4.2.6 on 2024-01-16 05:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='buyproduct',
            name='invoice_created',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
