# Generated by Django 4.2.10 on 2025-01-19 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('duration', models.IntegerField()),
                ('meeting_number', models.CharField(max_length=255)),
                ('encrypted_password', models.CharField(max_length=255)),
                ('join_url', models.TextField()),
                ('start_url', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField()),
                ('duration', models.IntegerField()),
                ('goal', models.CharField(max_length=100)),
                ('level', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('banner_image', models.ImageField(blank=True, null=True, upload_to='session_banner_images/', verbose_name='Session Banner Image')),
                ('current_participant_number', models.IntegerField(default=0)),
                ('total_participant_number', models.IntegerField()),
                ('price', models.IntegerField()),
                ('equipments', models.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Session',
                'verbose_name_plural': 'Sessions',
            },
        ),
    ]