from flask_login import UserMixin
from . import db
class User(UserMixin, db.Model):
    __tablename__ = 'sys_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='patient')
    id_card = db.Column(db.String(20), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'), nullable=True)
    patient = db.relationship('Patient', foreign_keys=[patient_id], backref=db.backref('user', uselist=False), lazy='joined')

class Doctor(db.Model):
    __tablename__ = 'doctor'
    doctor_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    title = db.Column(db.String(50))
    department = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('sys_user.id'), nullable=True)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('doctor', uselist=False), lazy='joined')

class Patient(db.Model):
    __tablename__ = 'patient'
    patient_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    birth_date = db.Column(db.Date)
    contact = db.Column(db.String(20))
    id_card = db.Column(db.String(20))
    insurance_card = db.Column(db.String(20))
    insurance_balance = db.Column(db.Float)
    #user = db.relationship('User', foreign_keys=[User.patient_id], uselist=False, lazy='joined')

class Schedule(db.Model):
    __tablename__ = 'schedule'
    schedule_id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.doctor_id'))
    date = db.Column(db.Date)
    time_slot = db.Column(db.String(20))
    reg_fee = db.Column(db.Float)
    room_address = db.Column(db.String(100))
    total_slots = db.Column(db.Integer)
    remain_slots = db.Column(db.Integer)
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id], backref=db.backref('schedules', lazy='dynamic'), lazy='joined')

class Registration(db.Model):
    __tablename__ = 'registration'
    registration_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.patient_id'))
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.schedule_id'))
    reg_time = db.Column(db.DateTime)
    visit_status = db.Column(db.String(20))
    patient = db.relationship('Patient', foreign_keys=[patient_id], backref=db.backref('registrations', lazy='dynamic'), lazy='joined')
    schedule = db.relationship('Schedule', foreign_keys=[schedule_id], backref=db.backref('registrations', lazy='dynamic'), lazy='joined')

class MedicalRecord(db.Model):
    __tablename__ = 'medical_record'
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.registration_id'), primary_key=True)
    visit_time = db.Column(db.DateTime, nullable=False)
    chief_complaint = db.Column(db.Text)
    present_illness = db.Column(db.Text)
    past_history = db.Column(db.Text)
    allergy_history = db.Column(db.Text)
    physical_exam = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    medication_details = db.relationship('MedicationDetail', backref='medical_record', lazy='dynamic')
    check_details = db.relationship('CheckDetail', backref='medical_record', lazy='dynamic')

class Drug(db.Model):
    __tablename__ = 'drug'
    drug_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specification = db.Column(db.String(100))
    price = db.Column(db.Float)
    usage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    stock = db.Column(db.Integer)
    remark = db.Column(db.String(200))
    status = db.Column(db.String(20))
    insurance_rate = db.Column(db.Float)

class CheckItem(db.Model):
    __tablename__ = 'check_item'
    item_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    department = db.Column(db.String(50))
    insurance_rate = db.Column(db.Float)

class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.registration_id'), nullable=True)
    fee_type = db.Column(db.String(50), nullable=False)
    insurance_amount = db.Column(db.Float, nullable=False)
    self_pay_amount = db.Column(db.Float, nullable=False)
    pay_method = db.Column(db.String(50), nullable=False)
    pay_time = db.Column(db.DateTime, nullable=False)
    pay_status = db.Column(db.String(50), nullable=False)



class MedicationDetail(db.Model):
    __tablename__ = 'medication_detail'
    detail_id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('medical_record.registration_id'))
    drug_id = db.Column(db.Integer, db.ForeignKey('drug.drug_id'))
    drug = db.relationship('Drug', foreign_keys=[drug_id], backref=db.backref('medication_details', lazy='dynamic'), lazy='joined')

class CheckDetail(db.Model):
    __tablename__ = 'check_detail'
    check_id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('medical_record.registration_id'))
    item_id = db.Column(db.Integer, db.ForeignKey('check_item.item_id'))
    result = db.Column(db.Text)
    check_item = db.relationship('CheckItem', foreign_keys=[item_id], backref=db.backref('check_details', lazy='dynamic'), lazy='joined')