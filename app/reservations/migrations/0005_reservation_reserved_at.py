# Generated by Django 2.2.14 on 2020-07-12 14:53

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0004_auto_20200712_0104'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='reserved_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
