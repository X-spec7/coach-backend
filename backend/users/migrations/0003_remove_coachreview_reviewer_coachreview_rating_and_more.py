# Generated by Django 4.2.10 on 2025-02-01 00:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_coachprofile_user_coachreview'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coachreview',
            name='reviewer',
        ),
        migrations.AddField(
            model_name='coachreview',
            name='rating',
            field=models.PositiveIntegerField(default=0, verbose_name='Review Rating'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='coachreview',
            name='reviewer_avatar',
            field=models.ImageField(blank=True, null=True, upload_to='user_images/', verbose_name='Review Avatar Image'),
        ),
        migrations.AddField(
            model_name='coachreview',
            name='reviewer_name',
            field=models.CharField(default=10, max_length=50, verbose_name='Reviewer Full Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='coachprofile',
            name='listed',
            field=models.BooleanField(default=True, help_text='Indicates whether the coach is approved by the admin', verbose_name='Listed'),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(default='John', max_length=50, verbose_name='First Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='full_name',
            field=models.CharField(default='John Doe', max_length=50, verbose_name='Full Name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(default='Doe', max_length=50, verbose_name='Last Name'),
        ),
    ]
