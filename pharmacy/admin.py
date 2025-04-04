from django.contrib import admin
from .models import Medicine, Prescription, PrescriptionItem

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1
    readonly_fields = ['item_price']

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date_prescribed', 'total_price', 'is_paid')
    list_filter = ('is_paid', 'doctor', 'date_prescribed')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__first_name', 'doctor__user__last_name')
    inlines = [PrescriptionItemInline]
    readonly_fields = ['total_price']

class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'quantity', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')

admin.site.register(Medicine, MedicineAdmin)
admin.site.register(Prescription, PrescriptionAdmin)