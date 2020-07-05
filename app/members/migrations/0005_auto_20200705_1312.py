# Generated by Django 2.2.13 on 2020-07-05 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_auto_20200705_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='time',
            field=models.CharField(blank=True, choices=[('00-10', '10시 이전'), ('10-13', '10시~13시'), ('13-16', '13시~16시'), ('16-18', '16시~18시'), ('18-21', '18시~21시'), ('21-00', '21시 이후')], max_length=20),
        ),
    ]