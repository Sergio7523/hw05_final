# Generated by Django 2.2.16 on 2022-10-10 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20221007_1618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(unique=True, verbose_name='уникальный идентификатор'),
        ),
    ]
