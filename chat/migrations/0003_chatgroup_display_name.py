# Generated by Django 5.1.6 on 2025-03-18 02:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_alter_chatgroup_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatgroup',
            name='display_name',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
