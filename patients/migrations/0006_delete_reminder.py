# Generated by Django 5.1.7 on 2025-03-31 07:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0005_reminder'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Reminder',
        ),
    ]
