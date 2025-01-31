# Generated by Django 4.2.10 on 2025-01-29 21:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workouts', '0002_classworkout_classworkoutdailyplan_and_more'),
        ('exercises', '0002_exercise_calorie_workoutexercise'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workoutexercise',
            name='daily_plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='workout_exercises', to='workouts.classworkoutdailyplan'),
        ),
    ]
