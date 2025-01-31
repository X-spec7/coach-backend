# Generated by Django 4.2.10 on 2025-01-29 17:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='recipient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contact',
            name='last_message',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contact_last_message', to='chat.message'),
        ),
        migrations.AddField(
            model_name='contact',
            name='user_one',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_one_contacts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contact',
            name='user_two',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_two_contacts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='contact',
            constraint=models.UniqueConstraint(condition=models.Q(('user_one__lt', models.F('user_two'))), fields=('user_one', 'user_two'), name='unique_contact_pair'),
        ),
    ]
