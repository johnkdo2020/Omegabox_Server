# Generated by Django 2.2.13 on 2020-06-28 14:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_kor', models.CharField(max_length=100)),
                ('name_eng', models.CharField(max_length=100)),
                ('code', models.PositiveIntegerField()),
                ('running_time', models.DurationField()),
                ('rank', models.IntegerField(unique=True)),
                ('acc_audience', models.PositiveIntegerField()),
                ('reservation_rate', models.FloatField()),
                ('open_date', models.DateField()),
                ('close_date', models.DateField()),
                ('grade', models.CharField(choices=[('all', '전체이용가'), ('12+', '12세 이상 관람가'), ('15+', '15세 이상 관람'), ('18+', '청소년 관람 불가')], max_length=20)),
                ('description', models.TextField(blank=True)),
                ('poster', models.ImageField(blank=True, upload_to='posters/')),
                ('trailer', models.FileField(blank=True, upload_to='trailers/')),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movies', to='movies.Genre')),
            ],
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('liked', models.BooleanField(default=False)),
                ('key_point', models.CharField(choices=[('actor', '배우'), ('prod', '연출'), ('story', '스토리'), ('visual', '영상미'), ('ost', 'OST')], max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to=settings.AUTH_USER_MODEL)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='movies.Movie')),
            ],
        ),
        migrations.AddField(
            model_name='movie',
            name='liked',
            field=models.ManyToManyField(related_name='movies', through='movies.Rating', to=settings.AUTH_USER_MODEL),
        ),
    ]
