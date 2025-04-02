from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, F, Q
from django.utils import timezone
from django.http import HttpResponseForbidden

from .models import Medicine, MedicineImportLog, Prescription, PrescriptionItem
from users.models import Doctors, Patients

@login_required(login_url='/login')
def medicine_list(request):
    """View all medicines in the pharmacy inventory"""
    medicines = Medicine.objects.all().order_by('name')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        medicines = medicines.filter(name__icontains=search_query)
    
    # Handle price update for staff
    if request.method == 'POST' and request.user.is_staff:
        medicine_id = request.POST.get('medicine_id')
        new_price = request.POST.get('new_price')
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            medicine.price = float(new_price)
            medicine.save()
            messages.success(request, f"Giá của thuốc {medicine.name} đã được cập nhật thành công.")
        except Medicine.DoesNotExist:
            messages.error(request, "Không tìm thấy thuốc.")
        except ValueError:
            messages.error(request, "Giá không hợp lệ.")
        
        return redirect('medicine_list')
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    elif request.user.is_doctor:
        base_template = 'doctors/base.html'
    else:
        base_template = 'patients/base.html'
    
    context = {
        'medicines': medicines,
        'search_query': search_query,
        'base_template': base_template,
    }
    return render(request, 'pharmacy/medicine_list.html', context)


@login_required(login_url='/login')
def add_medicine(request):
    """Add a new medicine to the inventory"""
    # Only allow staff to add medicines
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to perform this action")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    elif request.user.is_doctor:
        base_template = 'doctors/base.html'
    else:
        base_template = 'patients/base.html'
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        
        medicine = Medicine(
            name=name,
            description=description,
            price=price,
            quantity=quantity
        )
        medicine.save()
        
        messages.success(request, "New medicine added to inventory")
        return redirect('medicine_list')
    
    return render(request, 'pharmacy/add_medicine.html', {'base_template': base_template})


@login_required(login_url='/login')
def edit_medicine(request, medicine_id):
    """Edit an existing medicine"""
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to perform this action")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    elif request.user.is_doctor:
        base_template = 'doctors/base.html'
    else:
        base_template = 'patients/base.html'
    
    medicine = get_object_or_404(Medicine, id=medicine_id)
    
    if request.method == 'POST':
        medicine.name = request.POST.get('name')
        medicine.description = request.POST.get('description')
        medicine.price = request.POST.get('price')
        
        # Retain the original quantity instead of removing it
        # medicine.quantity = request.POST.get('quantity')  # Remove this line
        
        medicine.save()
        
        messages.success(request, "Medicine information updated")
        return redirect('medicine_list')
    
    return render(request, 'pharmacy/edit_medicine.html', {
        'medicine': medicine,
        'base_template': base_template
    })


@login_required(login_url='/login')
def medicine_import(request):
    """Import medicines into inventory"""
    # Only nurses and staff are allowed to perform this action
    if not hasattr(request.user, 'nurses') and not request.user.is_staff:
        return HttpResponseForbidden("Only nurses can perform this action")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    else:
        base_template = 'doctors/base.html'
    
    if request.method == 'POST':
        medicine_id = request.POST.get('medicine')
        quantity = int(request.POST.get('quantity'))
        import_price = float(request.POST.get('import_price'))
        
        # Get medicine information
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        # Determine the importer (nurse or current user)
        nurse = request.user.nurses if hasattr(request.user, 'nurses') else None
        
        # Update quantity and import price
        medicine.quantity += quantity
        medicine.import_price = import_price
        medicine.save()
        
        # Create import log
        import_log = MedicineImportLog.objects.create(
            medicine=medicine,
            quantity_imported=quantity,
            nurse=nurse,
            total_import_price=quantity * import_price
        )
        
        messages.success(request, f"Imported {quantity} {medicine.name} into inventory")
        return redirect('medicine_import')
    
    # Get list of medicines and import history
    medicines = Medicine.objects.all()
    import_logs = MedicineImportLog.objects.order_by('-import_date')[:10]
    
    context = {
        'medicines': medicines,
        'import_logs': import_logs,
        'base_template': base_template
    }
    
    return render(request, 'pharmacy/medicine_import.html', context)


@login_required(login_url='/login')
def medicine_import_report(request):
    """Generate a report of medicine imports"""
    # Only nurses and staff are allowed to perform this action
    if not hasattr(request.user, 'nurses') and not request.user.is_staff:
        return HttpResponseForbidden("Only nurses can perform this action")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    else:
        base_template = 'doctors/base.html'
    
    # Filter report by date
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    import_logs = MedicineImportLog.objects.all()
    
    if start_date and end_date:
        import_logs = import_logs.filter(
            import_date__range=[start_date, end_date]
        )
    
    # Calculate total import value
    total_import_value = import_logs.aggregate(
        total=Sum(F('quantity_imported') * F('medicine__import_price'))
    )['total'] or 0
    
    context = {
        'import_logs': import_logs,
        'total_import_value': total_import_value,
        'base_template': base_template
    }
    
    return render(request, 'pharmacy/medicine_import_report.html', context)


@login_required(login_url='/login')
def create_prescription(request):
    """Create a new prescription for a patient"""
    # Only doctors can create prescriptions
    if not hasattr(request.user, 'doctors'):
        return HttpResponseForbidden("Only doctors can prescribe medication")
    
    base_template = 'doctors/base.html'
    
    doctor = request.user.doctors
    medicines = Medicine.objects.filter(quantity__gt=0).order_by('name')
    patients = Patients.objects.all()
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        notes = request.POST.get('notes')
        
        # Get selected patient
        patient = get_object_or_404(Patients, user_id=patient_id)
        
        # Create prescription
        prescription = Prescription(
            patient=patient,
            doctor=doctor,
            notes=notes
        )
        prescription.save()
        
        # Get medicine items from form
        medicine_ids = request.POST.getlist('medicine')
        quantities = request.POST.getlist('quantity')
        instructions = request.POST.getlist('instructions')
        
        # Thêm debug thông tin
        print(f"Medicine IDs: {medicine_ids}")
        print(f"Quantities: {quantities}")
        print(f"Instructions: {instructions}")
        
        # Create prescription items
        for i in range(len(medicine_ids)):
            if i < len(quantities) and quantities[i] and int(quantities[i]) > 0:
                try:
                    medicine = Medicine.objects.get(id=medicine_ids[i])
                    
                    # Check if we have enough quantity in stock
                    if medicine.quantity >= int(quantities[i]):
                        # Create prescription item
                        instruction_text = instructions[i] if i < len(instructions) else ""
                        
                        item = PrescriptionItem(
                            prescription=prescription,
                            medicine=medicine,
                            quantity=int(quantities[i]),
                            instructions=instruction_text
                        )
                        item.save()
                        
                        # Deduct from inventory
                        medicine.quantity -= int(quantities[i])
                        medicine.save()
                        
                        print(f"Added {quantities[i]} of {medicine.name} to prescription")
                    else:
                        messages.error(request, f"Not enough {medicine.name} in stock (only {medicine.quantity} left)")
                        # If error, delete the prescription and redirect back
                        prescription.delete()
                        return redirect('create_prescription')
                except Medicine.DoesNotExist:
                    messages.error(request, f"Medicine with ID {medicine_ids[i]} does not exist")
                    prescription.delete()
                    return redirect('create_prescription')
                except Exception as e:
                    print(f"Error adding medicine: {str(e)}")
                    messages.error(request, f"Error adding medicine: {str(e)}")
                    prescription.delete()
                    return redirect('create_prescription')
                
        # Check if any items were added
        if prescription.items.count() == 0:
            messages.error(request, "No medications were added to the prescription")
            prescription.delete()
            return redirect('create_prescription')
            
        messages.success(request, "Prescription created successfully")
        return redirect('doctor_prescriptions')
    
    context = {
        'medicines': medicines,
        'patients': patients,
        'base_template': base_template
    }
    
    return render(request, 'pharmacy/create_prescription.html', context)


@login_required(login_url='/login')
def doctor_prescriptions(request):
    """View all prescriptions created by the logged-in doctor"""
    if not hasattr(request.user, 'doctors'):
        return HttpResponseForbidden("Only doctors can view the list of prescriptions")
    
    base_template = 'doctors/base.html'
    
    doctor = request.user.doctors
    prescriptions = Prescription.objects.filter(doctor=doctor).order_by('-date_prescribed')
    
    return render(request, 'pharmacy/doctor_prescriptions.html', {
        'prescriptions': prescriptions,
        'base_template': base_template
    })


@login_required(login_url='/login')
def pending_prescriptions(request):
    """
    View all prescriptions that haven't been paid yet.
    Only staff or nurses are allowed to access this page.
    """
    # Check if the user is staff or nurse
    if not request.user.is_staff:
        return HttpResponseForbidden("Only staff or nurses can access this page")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    else:
        base_template = 'doctors/base.html'  # Fallback for admin or other staff
    
    # Query all unpaid prescriptions, ordered by the date prescribed
    prescriptions = Prescription.objects.filter(is_paid=False).order_by('-date_prescribed')
    
    # Render the pending prescriptions template with the context
    return render(request, 'pharmacy/pending_prescriptions.html', {
        'prescriptions': prescriptions,
        'base_template': base_template
    })


@login_required(login_url='/login')
@login_required(login_url='/login')
def process_prescription(request, prescription_id):
    """Process payment for a prescription (mark as paid)"""
    if not request.user.is_staff:
        return HttpResponseForbidden("Only nurses or staff can perform this action")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    else:
        base_template = 'doctors/base.html'  # Fallback for admin or other staff
    
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    if request.method == 'POST':
        # Get the payment method
        payment_method = request.POST.get('payment_method', '')
        
        # Process based on payment method
        if payment_method == 'cash':
            # Get the cash received and change due from the form
            cash_received = request.POST.get('cash_received', 0)
            change_due = request.POST.get('change_due', 0)
            
            try:
                # Convert to float for validation
                cash_received_float = float(cash_received)
                
                # Validate the payment
                if cash_received_float < float(prescription.total_price):
                    messages.error(request, "Cash received must be at least equal to the total price.")
                    return redirect('process_prescription', prescription_id=prescription_id)
                
                # Mark the prescription as paid
                prescription.is_paid = True
                prescription.paid_date = timezone.now()
                
                # Save payment details in notes
                payment_details = f"\n\nPayment details:\nMethod: Cash\nCash received: {cash_received} VND\nChange due: {change_due} VND\nProcessed by: {request.user.first_name} {request.user.last_name}\nDate: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
                
                if prescription.notes:
                    prescription.notes += payment_details
                else:
                    prescription.notes = payment_details
                    
                prescription.save()
                
                messages.success(request, f"Cash payment processed for prescription of patient {prescription.patient.user.first_name} {prescription.patient.user.last_name}. Change given: {change_due} VND")
                return redirect('pending_prescriptions')
                
            except ValueError:
                messages.error(request, "Invalid payment amount entered.")
                return redirect('process_prescription', prescription_id=prescription_id)
        
        elif payment_method == 'online':
            # Get online payment details
            transaction_id = request.POST.get('transaction_id', '')
            payment_provider = request.POST.get('payment_provider', '')
            payment_notes = request.POST.get('payment_notes', '')
            
            # Validate transaction ID and payment provider
            if not transaction_id or not payment_provider:
                messages.error(request, "Transaction ID and payment provider are required for online payments.")
                return redirect('process_prescription', prescription_id=prescription_id)
            
            # Mark the prescription as paid
            prescription.is_paid = True
            prescription.paid_date = timezone.now()
            
            # Format payment provider name for display
            payment_provider_display = {
                'momo': 'MoMo',
                'zalopay': 'ZaloPay',
                'vnpay': 'VNPay',
                'bank_transfer': 'Bank Transfer',
                'credit_card': 'Credit Card',
                'other': 'Other'
            }.get(payment_provider, payment_provider)
            
            # Save payment details in notes
            payment_details = f"\n\nPayment details:\nMethod: Online ({payment_provider_display})\nTransaction ID: {transaction_id}\nAmount: {prescription.total_price} VND\nProcessed by: {request.user.first_name} {request.user.last_name}\nDate: {timezone.now().strftime('%d/%m/%Y %H:%M')}"
            
            if payment_notes:
                payment_details += f"\nNotes: {payment_notes}"
                
            if prescription.notes:
                prescription.notes += payment_details
            else:
                prescription.notes = payment_details
                
            prescription.save()
            
            messages.success(request, f"Online payment ({payment_provider_display}) processed for prescription of patient {prescription.patient.user.first_name} {prescription.patient.user.last_name}.")
            return redirect('pending_prescriptions')
        
        else:
            messages.error(request, "Invalid payment method.")
            return redirect('process_prescription', prescription_id=prescription_id)
    
    items = prescription.items.all()
    
    context = {
        'prescription': prescription,
        'items': items,
        'base_template': base_template
    }
    
    return render(request, 'pharmacy/process_prescription.html', context)


@login_required(login_url='/login')
def view_prescription(request, prescription_id):
    """View details of a specific prescription"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    elif request.user.is_doctor:
        base_template = 'doctors/base.html'
    else:
        base_template = 'patients/base.html'
    
    # Check permissions - only the doctor who created it, the patient it's for, or staff can view
    if (hasattr(request.user, 'doctors') and request.user.doctors == prescription.doctor) or \
       (hasattr(request.user, 'patients') and request.user.patients == prescription.patient) or \
       request.user.is_staff:
        
        items = prescription.items.all()
        
        context = {
            'prescription': prescription,
            'items': items,
            'base_template': base_template
        }
        
        return render(request, 'pharmacy/view_prescription.html', context)
    else:
        return HttpResponseForbidden("You do not have permission to view this prescription")


@login_required(login_url='/login')
def patient_prescriptions(request):
    """View all prescriptions for the logged-in patient"""
    if not hasattr(request.user, 'patients'):
        return HttpResponseForbidden("Only patients can view their prescription history")
    
    base_template = 'patients/base.html'
    
    patient = request.user.patients
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-date_prescribed')
    
    return render(request, 'pharmacy/patient_prescriptions.html', {
        'prescriptions': prescriptions,
        'base_template': base_template
    })


@login_required(login_url='/login')
def prescription_history(request):
    """
    View history of all paid prescriptions.
    Only staff or nurses are allowed to access this page.
    """
    # Check if the user is staff or nurse
    if not request.user.is_staff and not hasattr(request.user, 'nurses'):
        return HttpResponseForbidden("Only staff or nurses can access this page")
    
    # Determine the appropriate base template
    if hasattr(request.user, 'nurses'):
        base_template = 'nurses/base.html'
    else:
        base_template = 'doctors/base.html'  # Fallback for admin or other staff
    
    # Filter options
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    patient_name = request.GET.get('patient_name')
    doctor_name = request.GET.get('doctor_name')
    
    # Query all paid prescriptions, ordered by the paid date
    prescriptions = Prescription.objects.filter(is_paid=True).order_by('-paid_date')
    
    # Apply filters if provided
    if start_date:
        prescriptions = prescriptions.filter(paid_date__date__gte=start_date)
    
    if end_date:
        prescriptions = prescriptions.filter(paid_date__date__lte=end_date)
    
    if patient_name:
        prescriptions = prescriptions.filter(
            Q(patient__user__first_name__icontains=patient_name) | 
            Q(patient__user__last_name__icontains=patient_name)
        )
    
    if doctor_name:
        prescriptions = prescriptions.filter(
            Q(doctor__user__first_name__icontains=doctor_name) | 
            Q(doctor__user__last_name__icontains=doctor_name)
        )
    
    # Calculate total revenue
    total_revenue = prescriptions.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # Render the prescription history template with the context
    return render(request, 'pharmacy/prescription_history.html', {
        'prescriptions': prescriptions,
        'total_revenue': total_revenue,
        'start_date': start_date,
        'end_date': end_date,
        'patient_name': patient_name,
        'doctor_name': doctor_name,
        'base_template': base_template
    })
