# Generated by Django 5.1.6 on 2025-03-16 11:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0002_alter_post_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='like',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
