
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.orm import relationship


db = SQLAlchemy()  

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    email=db.Column(db.String(150), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='patient', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor_profile = relationship('Doctor', backref='user', uselist=False)
    patient_profile = relationship('Patient', backref='user', uselist=False)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Relationship: One Department has many Doctors
    doctors = relationship('Doctor', backref='department')


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    contact_number = db.Column(db.String(20))
    licence_number = db.Column(db.String(50), unique=True)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    # Relationships: One Doctor has many Appointments and Schedules
    appointments = relationship('Appointment', backref='doctor')
    schedules = relationship('DoctorSchedule', backref='doctor')

class DoctorSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False) # e.g., 'Monday'
    start_time = db.Column(db.Time, nullable=False) 
    end_time = db.Column(db.Time, nullable=False)

    
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to the User table (One-to-One)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    contact_number = db.Column(db.String(20))
    medical_history_summary = db.Column(db.Text)
    is_blacklisted = db.Column(db.Boolean, default=False)
    
    # Relationship: One Patient has many Appointments
    appointments = relationship('Appointment', backref='patient')


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Booked', nullable=False)
    
    # Relationship: One Appointment has one Treatment record
    treatment_record = relationship('Treatment', backref='appointment', uselist=False)

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key to the Appointment table (One-to-One)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), unique=True, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=False) # Stored as text/JSON string if complex
    notes = db.Column(db.Text)
    
    # Optional FK: Record who created the treatment (The Doctor)
    created_by_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    doctor_creator = relationship('Doctor', backref='created_treatments', foreign_keys=[created_by_doctor_id])

    
