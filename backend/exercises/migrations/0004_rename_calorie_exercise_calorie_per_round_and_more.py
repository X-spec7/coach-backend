# Generated by Django 4.2.10 on 2025-02-01 00:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0002_class_banner_image'),
        ('workouts', '0003_delete_workoutdailyplan_and_more'),
        ('exercises', '0003_alter_workoutexercise_daily_plan'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exercise',
            old_name='calorie',
            new_name='calorie_per_round',
        ),
        migrations.AlterField(
            model_name='workoutexercise',
            name='daily_plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_exercises', to='workouts.clientworkoutdailyplan'),
        ),
        migrations.AlterField(
            model_name='workoutexercise',
            name='exercise',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_exercise', to='exercises.exercise'),
        ),
        migrations.CreateModel(
            name='ClassExercise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('set_count', models.PositiveIntegerField(default=3, verbose_name='Set Count')),
                ('reps_count', models.PositiveIntegerField(default=10, verbose_name='Reps Count')),
                ('rest_duration', models.PositiveIntegerField(default=30, verbose_name='Rest Duration (seconds)')),
                ('calorie_per_set', models.PositiveIntegerField(default=50, verbose_name='Calorie Burnt per Set')),
                ('class_ref', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_exercises', to='classes.class')),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='class_exercise', to='exercises.exercise')),
            ],
            options={
                'verbose_name': 'Class Exercise',
                'verbose_name_plural': 'Class Exercises',
            },
        ),
    ]
