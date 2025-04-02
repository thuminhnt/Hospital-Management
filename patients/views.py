from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from datetime import datetime
from django.urls import reverse
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from users.models import Doctors, Specialty, Patients
from patients.models import Appointment, Time, Status
from doctors.models import Remainder  # Import model Remainder

User = get_user_model()


@login_required(login_url='/login')
def patient_dashboard(request):
    patient = request.user.patients  # Lấy thông tin bệnh nhân hiện tại

    # Lấy ngày hiện tại và ngày cuối tuần
    today = now().date()
    end_of_week = today + timedelta(days=7)

    # Lấy danh sách các reminder liên quan đến bệnh nhân trong tuần
    # Chỉ hiển thị các cuộc hẹn từ ngày hiện tại trở đi
    remainders = Remainder.objects.filter(
        appointment__patient=patient,
        date__range=[today, end_of_week],
        date__gte=today  # Chỉ lấy những cuộc hẹn từ ngày hiện tại trở đi
    )

    return render(request, 'patients/patient_dashboard.html', {
        'remainders': remainders,  # Truyền danh sách reminder vào template
    })


@login_required(login_url='/login')
def my_appointments(request):
    app = Appointment.objects.filter(patient__user=request.user)

    filter_status = request.GET.get('filter_status')
    filter_date = request.GET.get('filter_date')
    filter_doctor_name = request.GET.get('filter_doctor_name')
    appointment_id = request.GET.get('appointment_id')

    if filter_status and filter_status != 'All':
        app = app.filter(status__status=filter_status)

    if filter_date:
        app = app.filter(start_date=filter_date)

    if filter_doctor_name:
        app = app.filter(doctor__user__first_name__icontains=filter_doctor_name)

    # Nếu có appointment_id được truyền vào từ URL (khi click "View" từ remainder)
    highlighted_appointment = None
    if appointment_id:
        try:
            highlighted_appointment = int(appointment_id)
        except ValueError:
            highlighted_appointment = None

    return render(request, "patients/my_appointments.html", {
        'appointments': app,
        'filter_status': filter_status,
        'filter_date': filter_date,
        'filter_doctor_name': filter_doctor_name,
        'highlighted_appointment': highlighted_appointment
    })


@login_required(login_url='/login')
def book_appointment(request):
    specialities = Specialty.objects.all()
    doctors = Doctors.objects.all()

    filter_speciality = request.GET.get('filter_speciality')
    filter_city = request.GET.get('filter_city')
    filter_doctor_name = request.GET.get('filter_doctor_name')

    if filter_speciality and filter_speciality != 'All':
        doctors = doctors.filter(specialty__name=filter_speciality)

    if filter_doctor_name:
        doctors = doctors.filter(user__first_name__icontains=filter_doctor_name)

    if filter_city:
        doctors = doctors.filter(user__id_address__city__icontains=filter_city)

    return render(request, "patients/book_appointment.html", {
        'doctors': doctors,
        'specialities': specialities,
        'filter_speciality': filter_speciality,
        'filter_doctor_name': filter_doctor_name,
        'filter_city': filter_city,
    })


@login_required(login_url='/login')
def patient_confirm_book(request, doctor):
    print(doctor)
    if request.method == 'POST':
        date = request.POST.get("date")
        summary = request.POST.get("summary")
        description = request.POST.get("description")
        time = request.POST.get("time")
        heure = Time.objects.get(time=time)
        doctor = Doctors.objects.get(user__username=doctor)
        patient = Patients.objects.get(user=request.user)
        status = Status.objects.get(status="Waited")

        appointment = Appointment.objects.create(
            summary=summary,
            description=description,
            start_date=date,
            time=heure,
            doctor=doctor,
            patient=patient,
            status=status
        )

        if appointment:
            app = Appointment.objects.filter(patient__user=request.user)
            return render(request, 'patients/my_appointments.html', {"appointments": app})

    doc = Doctors.objects.get(user__username=doctor)
    if doc:
        times = Time.objects.all()
        return render(request, 'patients/patient_confirm_book.html', {'times': times, 'doctor': doc})

    doctors = Doctors.objects.all()
    return render(request, 'patients/book_appointment.html', {"doctors": doctors})


@login_required(login_url='/login')
def send_reminders(request):
    # Lấy thời gian hiện tại
    current_time = now()
    # Lấy các lịch hẹn trong vòng 24 giờ tới và chưa được nhắc nhở
    upcoming_appointments = Appointment.objects.filter(
        start_date__gte=current_time.date(),
        start_date__lte=(current_time + timedelta(days=1)).date(),
        reminder_sent=False
    )

    for appointment in upcoming_appointments:
        # Gửi email nhắc nhở
        send_mail(
            subject='Reminder: Upcoming Appointment',
            message=f'Dear {appointment.patient.user.first_name},\n\n'
                    f'You have an appointment with Dr. {appointment.doctor.user.first_name} '
                    f'on {appointment.start_date} at {appointment.time.time}.\n\n'
                    f'Please make sure to attend on time.\n\nThank you!',
            from_email='hospital@example.com',
            recipient_list=[appointment.patient.user.email],
            fail_silently=False,
        )

        # Đánh dấu đã gửi nhắc nhở
        appointment.reminder_sent = True
        appointment.save()

    messages.success(request, "Reminders sent successfully!")
    return redirect('patient_dashboard')  # Điều hướng về dashboard hoặc trang phù hợp


@login_required(login_url='/login')
def create_appointment(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        patient = request.user.patients
        summary = request.POST.get('summary')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        time_id = request.POST.get('time_id')

        doctor = Doctors.objects.get(id=doctor_id)
        time = Time.objects.get(id=time_id)

        # Tạo Appointment
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            summary=summary,
            description=description,
            start_date=start_date,
            time=time
        )
        messages.success(request, "Appointment created successfully!")
        return redirect('patient_dashboard')

    return render(request, 'patients/create_appointment.html')