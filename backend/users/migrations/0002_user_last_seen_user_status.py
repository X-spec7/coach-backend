# Generated by Django 4.2.10 on 2025-01-17 16:36

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_seen',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Last Seen'),
        ),
        migrations.AddField(
            model_name='user',
            name='status',
            field=models.CharField(choices=[('online', 'Online'), ('offline', 'Offline')], default='offline', max_length=50, verbose_name='Status'),
        ),
    ]