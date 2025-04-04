# Generated by Django 5.1.7 on 2025-03-28 11:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0001_initial'),
        ('users', '0014_nurses'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicine',
            name='expiry_date',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày hết hạn'),
        ),
        migrations.AddField(
            model_name='medicine',
            name='import_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Giá nhập'),
        ),
        migrations.AddField(
            model_name='medicine',
            name='manufacturing_date',
            field=models.DateField(blank=True, null=True, verbose_name='Ngày sản xuất'),
        ),
        migrations.AddField(
            model_name='medicine',
            name='minimum_stock',
            field=models.PositiveIntegerField(default=10, verbose_name='Số lượng tồn tối thiểu'),
        ),
        migrations.AddField(
            model_name='medicine',
            name='supplier',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Nhà cung cấp'),
        ),
        migrations.AlterField(
            model_name='medicine',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Giá bán'),
        ),
        migrations.CreateModel(
            name='MedicineImportLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_imported', models.PositiveIntegerField()),
                ('import_date', models.DateTimeField(auto_now_add=True)),
                ('total_import_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('medicine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pharmacy.medicine')),
                ('nurse', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.nurses')),
            ],
        ),
    ]
