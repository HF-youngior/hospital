from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import Schedule, Registration, Patient, Doctor, Payment, MedicalRecord, Drug, CheckItem, MedicationDetail, CheckDetail, db
from datetime import datetime
from sqlalchemy import desc

registration_bp = Blueprint('registration', __name__, url_prefix='/registration')

@registration_bp.route('/list')
@login_required
def registration_list():
    if current_user.role == 'admin':
        registrations = Registration.query.order_by(desc(Registration.reg_time)).all()
    elif current_user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            registrations = Registration.query.join(Schedule).filter(
                Schedule.doctor_id == doctor.doctor_id
            ).order_by(desc(Registration.reg_time)).all()
        else:
            registrations = []
    else:
        if current_user.patient_id:
            registrations = Registration.query.filter_by(
                patient_id=current_user.patient_id
            ).order_by(desc(Registration.reg_time)).all()
        else:
            registrations = []
    for reg in registrations:
        print(f"Registration ID: {reg.registration_id}, Schedule ID: {reg.schedule_id}, Schedule: {reg.schedule}")
    return render_template('registration_list.html', registrations=registrations, current_date=datetime.now().date())

@registration_bp.route('/available')
@login_required
@role_required('patient', 'admin')
def available_schedules():
    available_schedules = Schedule.query.filter(
        Schedule.remain_slots > 0,
        Schedule.date >= datetime.now().date()
    ).order_by(Schedule.date, Schedule.time_slot).all()
    for schedule in available_schedules:
        print(f"Available Schedule ID: {schedule.schedule_id}, Date: {schedule.date}, Time: {schedule.time_slot}, Remain Slots: {schedule.remain_slots}")
    return render_template('available_schedules.html', schedules=available_schedules)

@registration_bp.route('/make/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@role_required('patient', 'admin')
def make_registration(schedule_id):
    schedule = Schedule.query.get_or_404(schedule_id)
    if schedule.remain_slots <= 0:
        flash('对不起，该时段已无余号')
        return redirect(url_for('registration.available_schedules'))
    if schedule.date < datetime.now().date():
        flash('对不起，该排班日期已过')
        return redirect(url_for('registration.available_schedules'))

    patient_id = None
    if current_user.role == 'patient':
        if current_user.patient_id:
            patient_id = current_user.patient_id
        else:
            flash('您的账号未关联患者信息，请先完善个人信息')
            return redirect(url_for('patient.patient_profile'))
    elif current_user.role == 'admin':
        if request.method == 'POST':
            patient_id = request.form.get('patient_id', type=int)
        else:
            patients = Patient.query.all()
            return render_template('select_patient.html', patients=patients, schedule=schedule)

    if patient_id:
        # 检查患者是否已有“待就诊”状态的挂号
        existing = Registration.query.filter_by(
            patient_id=patient_id,
            schedule_id=schedule_id,
            visit_status='待就诊'
        ).first()
        if existing:
            flash('您已经有一条待就诊的挂号，请勿重复预约')
            return redirect(url_for('registration.available_schedules'))

        patient = Patient.query.get(patient_id)
        reg_fee = schedule.reg_fee
        insurance_rate = 0.8
        insurance_amount = reg_fee * insurance_rate
        self_pay_amount = reg_fee * (1 - insurance_rate)

        if patient.insurance_balance < insurance_amount:
            flash('医保余额不足以支付挂号费！')
            return redirect(url_for('registration.available_schedules'))

        try:
            registration = Registration(
                patient_id=patient_id,
                schedule_id=schedule_id,
                reg_time=datetime.now(),
                visit_status='待就诊'
            )
            schedule.remain_slots -= 1
            patient.insurance_balance -= insurance_amount
            print(f"Make Registration: Schedule ID: {schedule_id}, Remain Slots: {schedule.remain_slots}")

            payment = Payment(
                registration_id=registration.registration_id,
                fee_type='挂号费',
                insurance_amount=insurance_amount,
                self_pay_amount=self_pay_amount,
                pay_method='医保支付',
                pay_time=datetime.now(),
                pay_status='已支付'
            )
            db.session.add_all([registration, payment])
            db.session.commit()
            flash('挂号预约成功！')
            return redirect(url_for('registration.registration_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'预约挂号失败：{str(e)}')
            print(f"Error making registration: {str(e)}")
    return redirect(url_for('registration.available_schedules'))

@registration_bp.route('/cancel/<int:registration_id>', methods=['POST'])
@login_required
def cancel_registration(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if current_user.role == 'patient' and current_user.patient_id != registration.patient_id:
        flash('您无权取消此挂号')
        return redirect(url_for('registration.registration_list'))
    if registration.visit_status != '待就诊':
        flash('该挂号已完成就诊或已取消，无法再次取消')
        return redirect(url_for('registration.registration_list'))
    if registration.schedule.date < datetime.now().date():
        flash('预约日期已过，无法取消')
        return redirect(url_for('registration.registration_list'))

    try:
        # 查询挂号费支付记录
        payment = Payment.query.filter_by(
            registration_id=registration.registration_id,
            fee_type='挂号费',
            pay_status='已支付'
        ).first()
        if payment:
            patient = Patient.query.get(registration.patient_id)
            patient.insurance_balance += payment.insurance_amount
            db.session.delete(payment)

        # 更新挂号状态和余号
        registration.schedule.remain_slots += 1
        registration.visit_status = '已取消'
        print(f"Cancel Registration ID: {registration.registration_id}, Schedule ID: {registration.schedule_id}, New Remain Slots: {registration.schedule.remain_slots}")
        db.session.commit()
        flash('挂号已成功取消')
    except Exception as e:
        db.session.rollback()
        flash(f'取消挂号失败：{str(e)}')
        print(f"Error cancelling registration: {str(e)}")
    return redirect(url_for('registration.registration_list'))

@registration_bp.route('/pay/medication/<int:registration_id>', methods=['POST'])
@login_required
@role_required('patient')
def pay_medication(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if registration.patient_id != current_user.patient_id:
        flash('您无权操作此记录')
        return redirect(url_for('registration.registration_list'))

    medication_details = MedicationDetail.query.filter_by(registration_id=registration_id).all()
    if not medication_details:
        flash('没有需要支付的药品')
        return redirect(url_for('registration.registration_list'))

    patient = Patient.query.get(registration.patient_id)
    total_amount = 0
    for detail in medication_details:
        drug = Drug.query.get(detail.drug_id)
        total_amount += drug.price

    insurance_rate = sum([Drug.query.get(d.drug_id).insurance_rate for d in medication_details]) / len(medication_details)
    insurance_amount = total_amount * insurance_rate
    self_pay_amount = total_amount * (1 - insurance_rate)

    if patient.insurance_balance < insurance_amount:
        flash('医保余额不足')
        return redirect(url_for('registration.registration_list'))

    try:
        payment = Payment(
            registration_id=registration_id,
            fee_type='药品费',
            insurance_amount=insurance_amount,
            self_pay_amount=self_pay_amount,
            pay_method='医保支付',
            pay_time=datetime.now(),
            pay_status='已支付'
        )
        db.session.add(payment)
        patient.insurance_balance -= insurance_amount
        db.session.commit()
        flash('药品费用支付成功')
    except Exception as e:
        db.session.rollback()
        flash(f'药品费用支付失败：{str(e)}')
    return redirect(url_for('registration.registration_list'))

@registration_bp.route('/pay/check/<int:registration_id>', methods=['POST'])
@login_required
@role_required('patient')
def pay_check(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    if registration.patient_id != current_user.patient_id:
        flash('您无权操作此记录')
        return redirect(url_for('registration.registration_list'))

    check_details = CheckDetail.query.filter_by(registration_id=registration_id).all()
    if not check_details:
        flash('没有需要支付的检查项目')
        return redirect(url_for('registration.registration_list'))

    patient = Patient.query.get(registration.patient_id)
    total_amount = 0
    for detail in check_details:
        item = CheckItem.query.get(detail.item_id)
        total_amount += item.price

    insurance_rate = sum([CheckItem.query.get(d.item_id).insurance_rate for d in check_details]) / len(check_details)
    insurance_amount = total_amount * insurance_rate
    self_pay_amount = total_amount * (1 - insurance_rate)

    if patient.insurance_balance < insurance_amount:
        flash('医保余额不足')
        return redirect(url_for('registration.registration_list'))

    try:
        payment = Payment(
            registration_id=registration_id,
            fee_type='检查费',
            insurance_amount=insurance_amount,
            self_pay_amount=self_pay_amount,
            pay_method='医保支付',
            pay_time=datetime.now(),
            pay_status='已支付'
        )
        db.session.add(payment)
        patient.insurance_balance -= insurance_amount
        db.session.commit()
        flash('检查费用支付成功')
    except Exception as e:
        db.session.rollback()
        flash(f'检查费用支付失败：{str(e)}')
    return redirect(url_for('registration.registration_list'))

@registration_bp.route('/medicalrecord/<int:registration_id>', endpoint='registration_view_medical_record')
@login_required
@role_required('patient')
def view_medical_record(registration_id):
    record = MedicalRecord.query.filter_by(registration_id=registration_id).first_or_404()
    registration = Registration.query.get_or_404(registration_id)
    if registration.patient_id != current_user.patient_id:
        flash('您无权查看此记录')
        return redirect(url_for('registration.registration_list'))

    for detail in record.medication_details:
        payment = Payment.query.filter_by(
            registration_id=registration_id,
            fee_type='药品费',
            pay_status='已支付'
        ).first()
        detail.is_paid = bool(payment)

    for detail in record.check_details:
        payment = Payment.query.filter_by(
            registration_id=registration_id,
            fee_type='检查费',
            pay_status='已支付'
        ).first()
        detail.is_paid = bool(payment)

    return render_template('medical_record_view.html', record=record)