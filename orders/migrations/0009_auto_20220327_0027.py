# Generated by Django 3.1 on 2022-03-26 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_auto_20220327_0027'),
        ('orders', '0008_auto_20220326_1852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderproduct',
            name='variation',
            field=models.ManyToManyField(blank=True, to='store.Variation'),
        ),
    ]
