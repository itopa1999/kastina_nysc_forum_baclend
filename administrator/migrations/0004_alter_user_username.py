# Generated by Django 5.1.6 on 2025-03-13 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0003_userverification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
