# Generated by Django 5.1.7 on 2025-03-31 07:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_medicinetiming_remainder'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='remainder',
            name='patient',
        ),
        migrations.DeleteModel(
            name='MedicineTiming',
        ),
        migrations.DeleteModel(
            name='Remainder',
        ),
    ]
