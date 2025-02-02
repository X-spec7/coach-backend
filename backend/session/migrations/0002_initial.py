# Generated by Django 4.2.10 on 2025-01-29 17:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('session', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='booked_users',
            field=models.ManyToManyField(related_name='booked_sessions', to=settings.AUTH_USER_MODEL, verbose_name='Booked Users'),
        ),
        migrations.AddField(
            model_name='session',
            name='coach',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session', to=settings.AUTH_USER_MODEL, verbose_name='Session Creator'),
        ),
        migrations.AddField(
            model_name='session',
            name='meeting',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='session.meeting', verbose_name=''),
        ),
        migrations.AddField(
            model_name='meeting',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_creator', to=settings.AUTH_USER_MODEL),
        ),
    ]
