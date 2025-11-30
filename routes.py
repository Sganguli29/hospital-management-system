from flask import render_template,request,redirect, url_for,flash, session
from model import db, User, Doctor, Department, DoctorSchedule,Appointment, Patient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from sqlalchemy.orm import aliased
from sqlalchemy import or_ # NEW


# --- START Decorator ---
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is logged in
            if 'user_id' not in session:
                flash('Please log in to continue.')
                return redirect(url_for('patient_login'))
            
            # Check if the user's role is in the allowed list
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash('Access denied. Insufficient privileges.')
                return redirect(url_for('patient_login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def init_routes(app):
    @app.route('/')
    def index():
        if 'user_id' in session:
            return render_template('register.html')
        else:
            flash('Please log in to continue.')
            return redirect(url_for('patient_login'))
    
    @app.route('/patient-login')
    def patient_login():
        return render_template('patient-login.html')
    
    @app.route('/patient-login',methods=['POST'])
    def patient_login_post():
        username = request.form.get('username')
        password = request.form.get('password')  
        
        user= User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash,password):
            flash('Invalid username or password.')
            return redirect(url_for('patient_login'))
        
        session['user_id'] = user.id     
        session['role'] = 'patient'
        return redirect(url_for('patient_dashboard'))
    


    @app.route('/doctor-admin-login')
    def doctor_admin_login():
        return render_template('doctor-admin-login.html') 

    @app.route('/doctor-admin-login',methods=['POST'])
    def doctor_admin_login_post():
        username = request.form.get('username')
        password = request.form.get('password')  
        
        user= User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password_hash,password):
            flash('Invalid username or password.')
            return redirect(url_for('doctor_admin_login'))
        role = user.role.lower()
        if role == 'admin':
            session['user_id'] = user.id     
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))  
        elif role == 'doctor':
            session['user_id'] = user.id     
            session['role'] = 'doctor'
            return redirect(url_for('doctor_dashboard')) 
    
    @app.route('/register')
    def register():      
        return render_template('register.html')                             
    
    @app.route('/patient-dashboard',methods=['GET','POST'])
    @role_required(['patient'])
    def patient_dashboard():   
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            return render_template('patient.html', patient_name=user.full_name, user=user)
        else:
            session.pop('user_id', None) 
            session.pop('role', None)
            flash('User data not found.')
            return redirect(url_for('patient_login'))


    @app.route('/admin-dashboard')
    @role_required(['admin'])
    def admin_dashboard(): 
        user_id = session['user_id']
        user = User.query.get(user_id)
        all_doctors = db.session.query(User, Doctor, Department) \
                    .join(Doctor, User.id == Doctor.user_id) \
                    .join(Department, Doctor.specialization_id == Department.id) \
                    .all()
        
        all_schedules = db.session.query(DoctorSchedule, Doctor, User) \
                        .join(Doctor, DoctorSchedule.doctor_id == Doctor.id) \
                        .join(User, Doctor.user_id == User.id) \
                        .order_by(User.full_name, DoctorSchedule.day_of_week) \
                        .all()
        
        PatientUser = aliased(User)
        DoctorUser = aliased(User)

        all_appointments = db.session.query(
        Appointment,
        PatientUser.full_name.label('patient_name'),
        DoctorUser.full_name.label('doctor_name')
        ) \
        .join(Patient, Appointment.patient_id == Patient.id) \
        .join(Doctor, Appointment.doctor_id == Doctor.id) \
        .join(PatientUser, Patient.user_id == PatientUser.id) \
        .join(DoctorUser, Doctor.user_id == DoctorUser.id) \
        .order_by(Appointment.start_time.desc()) \
        .all()

# Pass data to template:
        total_appointments = Appointment.query.count()
    # 2. Fetch dashboard counts
        total_doctors = Doctor.query.count()
        total_patients = User.query.filter_by(role='patient').count()
    # Placeholder for appointments count (as you don't have appointment creation logic yet)
    
        return render_template('admin.html', 
                               appointments=all_appointments,
                           doctors=all_doctors, 
                           schedules=all_schedules,
                           total_doctors=total_doctors,
                           total_patients=total_patients,
                           total_appointments=total_appointments,admin_name=user.full_name,user=user
                        )       
        
       
    
    @app.route('/doctor-dashboard')
    @role_required(['doctor'])
    def doctor_dashboard():  
        return render_template('doctor.html')
    
    @app.route('/register',methods=['POST'])
    def register_post():  
        username = request.form.get('username')
        password = request.form.get('password')  
        email= request.form.get('email')
        full_name= request.form.get('full_name')  
        confirm_password= request.form.get('confirm_password')
    
        if not username or not password or not email or not full_name or not confirm_password:
            flash('Please fill out all fields.')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.')        
            return redirect(url_for('register'))
        user= User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('register'))
        
        password_hash= generate_password_hash(password)

        new_user= User(full_name=full_name,username=username,
                       email=email,password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('patient_login'))
    # routes.py

    @app.route('/logout')
    def logout():
      
    # Remove user session keys
      user_role = session.get('role')
      session.pop('user_id', None)
      session.pop('role', None)
      

      if user_role == 'admin' or user_role == 'doctor':
          flash('You have been logged out successfully.')
          # Redirect to the doctor/admin login page
          return redirect(url_for('doctor_admin_login'))
      else: 
            flash('You have been logged out successfully.')
            # Redirect to the patient login page
            return redirect(url_for('patient_login'))  
          
    # routes.py

    @app.route('/patient-profile', methods=['GET', 'POST'])
    @role_required(['patient'])
    def patient_profile():
        user_id = session['user_id']
        user = User.query.get(user_id)
    
        if not user:
            session.pop('user_id', None)
            session.pop('role', None)
            flash('Your user data could not be found. Please log in again.', 'error')
            return redirect(url_for('patient_login'))
    
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            user.full_name = full_name or user.full_name
            user.email = email or user.email
        
            if new_password:
            
                if new_password != confirm_password:
                    flash('New password and confirmation do not match.', 'error')
                    return render_template('patient-profile.html', user=user)            
                if not current_password or not check_password_hash(user.password_hash, current_password):
                    flash('Incorrect current password. Password was not changed.', 'error')
                    return render_template('patient-profile.html', user=user)

                user.password_hash = generate_password_hash(new_password)
                flash('Profile and password updated successfully!', 'success')
                return render_template('patient-profile.html', user=user)
        
            else:
                flash('Profile updated successfully!', 'success')
                

            db.session.commit()
        
            return redirect(url_for('patient_profile')) 

        return render_template('patient-profile.html', user=user)
    
    @app.route('/doctor-profile', methods=['GET', 'POST'])
    @role_required(['doctor'])
    def doctor_profile():
        user_id = session['user_id']
        user = User.query.get(user_id)
    
        if not user:
            session.pop('user_id', None)
            session.pop('role', None)
            flash('Your user data could not be found. Please log in again.', 'error')
            return redirect(url_for('doctor_admin_login'))
    
        if request.method == 'POST':
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            user.full_name = full_name or user.full_name
            user.email = email or user.email
        
            if new_password:
            
                if new_password != confirm_password:
                    flash('New password and confirmation do not match.', 'error')
                    return render_template('patient-profile.html', user=user)            
                if not current_password or not check_password_hash(user.password_hash, current_password):
                    flash('Incorrect current password. Password was not changed.', 'error')
                    return render_template('patient-profile.html', user=user)

                user.password_hash = generate_password_hash(new_password)
                flash('Profile and password updated successfully!', 'success')
                return render_template('patient-profile.html', user=user)
        
            else:
                flash('Profile updated successfully!', 'success')
                

            db.session.commit()
        
            return redirect(url_for('patient_profile')) 

        return render_template('patient-profile.html', user=user)

    @app.route('/manage-doctor', methods=['POST'])
    def manage_doctor_post():
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') 
        contact_number = request.form.get('contact_number')
        specialization_name = request.form.get('specialization_name') 
        doctor_id = request.form.get('doctor_id') 

        if not full_name or not username or not contact_number or not specialization_name:
            flash('Missing required fields.', 'error')
            return redirect(url_for('admin_dashboard'))

    # 1. Find or create the Department/Specialization
        department = Department.query.filter_by(name=specialization_name).first()
        if not department:
            department = Department(name=specialization_name)
            db.session.add(department)
            db.session.commit()

        if doctor_id:
    # --- UPDATE DOCTOR LOGIC ---
            doctor = Doctor.query.get(doctor_id)
            if not doctor:
             flash(f"Doctor ID {doctor_id} not found.", "error")
             return redirect(url_for('admin_dashboard'))

            user = User.query.get(doctor.user_id)

            user.full_name = full_name or user.full_name
            user.username = username or user.username
            user.email = email or user.email

            if password:
                user.password_hash = generate_password_hash(password)

            doctor.specialization_id = department.id
            doctor.contact_number = contact_number or doctor.contact_number

            db.session.commit()
            flash(f"Doctor {user.full_name} updated successfully.", "success")
            return redirect(url_for('admin_dashboard'))

# --- ADD NEW DOCTOR LOGIC ---
        if not password or not email:
            flash("Email and Password are required for adding a new doctor.", "error")
            return redirect(url_for('admin_dashboard'))

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash("Username or Email already exists.", "error")
            return redirect(url_for('admin_dashboard'))

        password_hash = generate_password_hash(password)
        new_user = User(
        full_name=full_name,
        username=username,
        email=email,
        password_hash=password_hash,
        role='doctor'
        )
        db.session.add(new_user)
        db.session.flush()

        newdoctor = Doctor(
        user_id=new_user.id,
        specialization_id=department.id,
        contact_number=contact_number
        )
        db.session.add(newdoctor)
        db.session.commit()
        flash(f"New Doctor {full_name} added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/delete-doctor/<int:doctor_id>', methods=['POST'])
    @role_required(['admin'])
    def delete_doctor(doctor_id):
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash(f"Doctor ID {doctor_id} not found.", "error")
            return redirect(url_for('admin_dashboard'))

        user = User.query.get(doctor.user_id)

    # Delete doctor profile (and optionally the user)
        db.session.delete(doctor)

    # If each doctor has a dedicated User row, you probably want to delete that too:
        if user:
            db.session.delete(user)

        db.session.commit()
        flash("Doctor deleted successfully.", "success")
        return redirect(url_for('admin_dashboard'))
    

    @app.route('/manage-schedule', methods=['GET', 'POST'])
    @role_required(['admin'])
    def manage_schedule():
        
        if request.method == 'POST':
            doctor_id = request.form.get('schedule_doctor_id')
            day_of_week = request.form.get('day_of_week')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            schedule_id = request.form.get('schedule_id')
            
            if not doctor_id or not day_of_week or not start_time or not end_time:
                flash('Missing required schedule fields.', 'error')
                return redirect(url_for('admin_dashboard'))

            # Convert time strings to time objects
            try:
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            except ValueError:
                flash('Invalid time format. Use HH:MM.', 'error')
                return redirect(url_for('admin_dashboard'))

            if end_time_obj <= start_time_obj:
                flash('End time must be after start time.', 'error')
                return redirect(url_for('admin_dashboard'))

            if schedule_id:
                # --- FIX APPLIED HERE ---
                schedule = DoctorSchedule.query.get(schedule_id)
                if schedule:
                    # Crucial: Update the doctor_id in case the selected doctor changed
                    schedule.doctor_id = doctor_id 
                    schedule.day_of_week = day_of_week
                    schedule.start_time = start_time_obj
                    schedule.end_time = end_time_obj
                    db.session.commit() 
                    flash('Doctor schedule updated successfully!', 'success')
                else:
                    flash('Schedule entry not found.', 'error')
            else:
                # Add new schedule
                new_schedule = DoctorSchedule(
                    doctor_id=doctor_id,
                    day_of_week=day_of_week,
                    start_time=start_time_obj,
                    end_time=end_time_obj
                )
                db.session.add(new_schedule)
                db.session.commit()
                flash('New doctor schedule added successfully!', 'success')
            
            return redirect(url_for('admin_dashboard'))

        # GET request: Prepare data for a schedule management view (not implemented in admin.html)
        # For this exercise, GET requests should redirect to the dashboard.
        flash('Schedule management should be done via the dashboard form.', 'warning')
        return redirect(url_for('admin_dashboard'))

    @app.route('/delete-schedule/<int:schedule_id>', methods=['POST'])
    @role_required(['admin'])
    def delete_schedule(schedule_id):
        schedule = DoctorSchedule.query.get(schedule_id)
        if not schedule:
            flash(f"Schedule ID {schedule_id} not found.", "error")
            return redirect(url_for('admin_dashboard'))

        db.session.delete(schedule)
        db.session.commit()
        flash("Doctor schedule deleted successfully.", "success")
        return redirect(url_for('admin_dashboard'))

    @app.route('/update-appointment-status/<int:appointment_id>', methods=['POST'])
    @role_required(['admin'])
    def update_appointment_status(appointment_id):
        new_status = request.form.get('new_status')
        
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            flash(f"Appointment ID {appointment_id} not found.", "error")
            return redirect(url_for('admin_dashboard'))
        
        valid_statuses = ['Booked', 'Confirmed', 'Canceled', 'Completed']
        if new_status not in valid_statuses:
            flash(f"Invalid status: {new_status}. Must be one of: {', '.join(valid_statuses)}", "error")
            return redirect(url_for('admin_dashboard'))
            
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment {appointment_id} status updated to {new_status}.", "success")
        return redirect(url_for('admin_dashboard'))
    

    @app.route('/search-users', methods=['POST'])
    @role_required(['admin'])
    def search_users():
        query = request.form.get('query', '').strip()
        
        if not query:
            flash("Please enter a search term.", "warning")
            return redirect(url_for('admin_dashboard'))

        search_term_like = f'%{query}%'
        search_term_int = None
        try:
            # Check if the query is a valid integer for searching by ID
            search_term_int = int(query)
        except ValueError:
            pass
            
        # 1. Search for Doctors by Name and Specialization
        search_results_doctors = db.session.query(User, Doctor, Department) \
            .join(Doctor, User.id == Doctor.user_id) \
            .join(Department, Doctor.specialization_id == Department.id) \
            .filter(
                or_(
                    User.full_name.ilike(search_term_like),
                    Department.name.ilike(search_term_like)
                )
            ).all()

        # 2. Search for Patients by Name, ID, or Contact
        search_results_patients = db.session.query(User, Patient) \
            .join(Patient, User.id == Patient.user_id) \
            .filter(
                User.role == 'patient',
                or_(
                    User.full_name.ilike(search_term_like),
                    Patient.contact_number.ilike(search_term_like),
                    # Filter by Patient ID only if the query is a convertible integer
                    (Patient.id == search_term_int) if search_term_int is not None else False 
                )
            ).all()

        # --- Re-fetch required dashboard context data ---
        all_doctors = db.session.query(User, Doctor, Department) \
                    .join(Doctor, User.id == Doctor.user_id) \
                    .join(Department, Doctor.specialization_id == Department.id) \
                    .all()
        
        all_schedules = db.session.query(DoctorSchedule, Doctor, User) \
                        .join(Doctor, DoctorSchedule.doctor_id == Doctor.id) \
                        .join(User, Doctor.user_id == User.id) \
                        .order_by(User.full_name, DoctorSchedule.day_of_week) \
                        .all()

        PatientUser = aliased(User)
        DoctorUser = aliased(User)
        
        all_appointments = db.session.query(
            Appointment,
            PatientUser.full_name.label('patient_name'),
            DoctorUser.full_name.label('doctor_name')
        ) \
        .join(Patient, Appointment.patient_id == Patient.id) \
        .join(Doctor, Appointment.doctor_id == Doctor.id) \
        .join(PatientUser, Patient.user_id == PatientUser.id) \
        .join(DoctorUser, Doctor.user_id == DoctorUser.id) \
        .order_by(Appointment.start_time.desc()) \
        .all()
        

        total_doctors = Doctor.query.count()
        total_patients = User.query.filter_by(role='patient').count()
        total_appointments = Appointment.query.count() 
        user_info = User.query.get(session['user_id'])


        # Render admin.html, passing the search results
        flash(f"Search results for '{query}' shown below.", "success")
        return render_template('admin.html', 
                           doctors=all_doctors, 
                           schedules=all_schedules,
                           appointments=all_appointments,
                           total_doctors=total_doctors,
                           total_patients=total_patients,
                           total_appointments=total_appointments,
                           admin_name=user_info.full_name,
                           user=user_info,
                           search_results_doctors=search_results_doctors,
                           search_results_patients=search_results_patients
                        )

    # NEW ROUTE: Blacklist or Permanently Remove User (Doctor or Patient)
    @app.route('/manage-blacklist', methods=['POST'])
    @role_required(['admin'])
    def manage_blacklist():
        target_id_str = request.form.get('target_id', '').strip()
        action = request.form.get('action') # 'blacklist' or 'remove'
        
        if not target_id_str or not action:
            flash("Missing User ID or Action.", "error")
            return redirect(url_for('admin_dashboard'))

        try:
            target_id = int(target_id_str)
        except ValueError:
            flash("Invalid User ID format. Must be a number.", "error")
            return redirect(url_for('admin_dashboard'))

        # Find the user by ID
        target_user = User.query.get(target_id)
        
        if not target_user:
            flash(f"User ID {target_id} not found.", "error")
            return redirect(url_for('admin_dashboard'))
        
        # Safety check: Prevent admin from modifying their own account
        if target_user.id == session.get('user_id'):
            flash("Cannot blacklist or remove your own admin account.", "error")
            return redirect(url_for('admin_dashboard'))

        
        user_role = target_user.role

        if action == 'blacklist':
            # Toggle blacklisted status on the specific profile (Doctor/Patient)
            if user_role == 'doctor':
                profile = Doctor.query.filter_by(user_id=target_id).first()
                if profile:
                    new_status = not profile.is_blacklisted
                    profile.is_blacklisted = new_status
                    flash(f"Doctor {target_user.full_name} profile has been {'Blacklisted' if new_status else 'Activated'}.", "success")
                else:
                    flash(f"Doctor profile not found for user ID {target_id}.", "error")
            
            elif user_role == 'patient':
                profile = Patient.query.filter_by(user_id=target_id).first()
                if profile:
                    new_status = not profile.is_blacklisted
                    profile.is_blacklisted = new_status
                    flash(f"Patient {target_user.full_name} profile has been {'Blacklisted' if new_status else 'Activated'}.", "success")
                else:
                    flash(f"Patient profile not found for user ID {target_id}.", "error")
            
            else:
                 flash("Cannot blacklist users with this role.", "error")


        elif action == 'remove':
            # Permanent Removal: Delete associated profiles and then the User record
            
            if user_role == 'doctor' and target_user.doctor_profile:
                # Must delete dependent records first
                DoctorSchedule.query.filter_by(doctor_id=target_user.doctor_profile.id).delete()
                # Assuming cascade settings handle Appointment/Treatment records, we delete the profile
                db.session.delete(target_user.doctor_profile)
                
            elif user_role == 'patient' and target_user.patient_profile:
                # Assuming cascade settings handle Appointment/Treatment records, we delete the profile
                db.session.delete(target_user.patient_profile)
                
            # Finally, delete the User record
            db.session.delete(target_user)
            flash(f"{user_role.capitalize()} {target_user.full_name} and associated records have been permanently removed.", "success")
            
        else:
            flash("Invalid action specified.", "error")
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
        