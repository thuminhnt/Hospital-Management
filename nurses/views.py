from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from pharmacy.models import Medicine, Prescription
from django.contrib import messages

@login_required(login_url='/login')
def nurse_dashboard(request):
    """Dashboard tổng quan cho y tá"""
    # Thống kê dữ liệu cho dashboard
    total_medicines = Medicine.objects.count()
    low_stock_medicines = Medicine.objects.filter(quantity__lte=10).count()
    low_stock_medicines_list = Medicine.objects.filter(quantity__lte=10)
    pending_prescriptions = Prescription.objects.filter(is_paid=False).count()
    total_prescriptions = Prescription.objects.count()
    
    context = {
        'total_medicines': total_medicines,
        'low_stock_medicines': low_stock_medicines,
        'low_stock_medicines_list': low_stock_medicines_list,
        'pending_prescriptions': pending_prescriptions,
        'total_prescriptions': total_prescriptions,
    }
    
    return render(request, 'nurses/nurse_dashboard.html', context)

@login_required(login_url='/login')
def nurse_profile(request):
    user = request.user
    
    if request.method == 'POST':
        # For debugging - print all POST data
        print("POST data:", request.POST)
        print("FILES data:", request.FILES)
        
        # Xử lý cập nhật ảnh đại diện
        if 'profile_pic' in request.FILES:
            try:
                user.profile_avatar = request.FILES['profile_pic']
                user.save()
                messages.success(request, 'Profile picture updated successfully')
            except Exception as e:
                messages.error(request, f'Error updating profile picture: {str(e)}')
            return redirect('nurse_profile')
        
        # Xử lý cập nhật thông tin cá nhân
        try:
            # Check if the form is properly submitted with all required fields
            form_type = request.POST.get('form_type')
            if form_type == 'personal_info':
                # Get personal info fields
                first_name = request.POST.get('user_firstname', '')
                last_name = request.POST.get('user_lastname', '')
                gender = request.POST.get('user_gender', '')
                department = request.POST.get('department', '')
                
                # Address fields
                address_line = request.POST.get('address_line', '')
                region = request.POST.get('region', '')
                city = request.POST.get('city', '')
                code_postal = request.POST.get('code_postal', '')
                
                # Validate required fields and track which fields are empty
                field_errors = {}
                if not first_name.strip():
                    field_errors['first_name'] = True
                if not last_name.strip():
                    field_errors['last_name'] = True
                if not gender.strip():
                    field_errors['gender'] = True
                if not department.strip():
                    field_errors['department'] = True
                if not address_line.strip():
                    field_errors['address_line'] = True
                if not region.strip():
                    field_errors['region'] = True
                if not city.strip():
                    field_errors['city'] = True
                if not code_postal.strip():
                    field_errors['code_postal'] = True
                
                if field_errors:
                    messages.error(request, 'Please fill in all the required fields marked in red.')
                    context = {
                        'user': user,
                        'base_template': 'nurses/base.html',
                        'field_errors': field_errors
                    }
                    return render(request, 'nurses/nurse_profile.html', context)
                
                # Update user info
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                
                # Fix for the birthday field
                birthday = request.POST.get('birthday')
                if birthday and birthday.strip():  # Check if birthday is not empty
                    user.birthday = birthday
                
                # Update address
                address = user.id_address
                address.address_line = address_line
                address.region = region
                address.city = city
                address.code_postal = code_postal
                address.save()
                
                # Update nurse info
                nurse_profile = user.nurses
                nurse_profile.department = department
                nurse_profile.save()
                
                # Save user
                user.save()
                
                messages.success(request, 'Personal information updated successfully')
            else:
                # If form_type is not specified, show an error
                messages.error(request, 'Invalid form submission')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        
        return redirect('nurse_profile')
    
    context = {
        'user': user,
        'base_template': 'nurses/base.html',
        'field_errors': {}  # Empty by default
    }
    
    return render(request, 'nurses/nurse_profile.html', context)