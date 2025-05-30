from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import MedicalRecord, Registration, Schedule, MedicationDetail, CheckDetail, Drug, CheckItem, db
from datetime import datetime, date

medicalrecord = Blueprint('medicalrecord', __name__)


@medicalrecord.route('/medicalrecord', endpoint='medicalrecord_list')
@role_required('doctor')
@login_required
def list():
    if current_user.role == 'doctor' and current_user.doctor:
        # 获取当前医生的排班
        schedules = current_user.doctor.schedules.filter(
            Schedule.date == date.today()
        )
        print(f"Doctor: {current_user.doctor.name}, Schedules: {schedules.count()}")
        # 获取今天的挂号记录（包括待就诊和已就诊）
        registrations = Registration.query.filter(
            Registration.schedule_id.in_([s.schedule_id for s in schedules])
        ).all()
        print(f"Today's Registrations: {len(registrations)}")
    else:
        registrations = []
        print("No registrations found for this doctor.")

    return render_template('medicalrecord.html', registrations=registrations)

@medicalrecord.route('/medicalrecord/consult/<int:registration_id>', methods=['GET'])
@role_required('doctor')
@login_required
def consult(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    patient_id = registration.patient_id
    drugs = Drug.query.all()
    check_items = CheckItem.query.all()
    return render_template('medicalrecord.html', record=None, patient_id=patient_id, registration_id=registration_id,
                           drugs=drugs, check_items=check_items)


@medicalrecord.route('/medicalrecord/save', methods=['POST'])
def save():
    record_id = request.form.get('record_id')
    if record_id:
        record = MedicalRecord.query.get(record_id)
    else:
        record = MedicalRecord()

    record.patient_id = request.form.get('patient_id')
    record.chief_complaint = request.form.get('chief_complaint')
    record.present_illness = request.form.get('present_illness')
    record.past_history = request.form.get('past_history')
    record.allergy_history = request.form.get('allergy_history')
    record.physical_exam = request.form.get('physical_exam')
    record.diagnosis = request.form.get('diagnosis')
    record.suggestion = request.form.get('suggestion')
    registration_id = request.form.get('registration_id')
    if registration_id:
        record.registration_id = int(registration_id)
    else:
        return "挂号ID不能为空", 400

    # 处理用药明细
    medication_details = []
    i = 0
    while f'medication_drug_id_{i}' in request.form:
        drug_id = request.form.get(f'medication_drug_id_{i}')
        if drug_id:
            detail = MedicationDetail(
                record_id=record.id if record_id else None,
                drug_id=int(drug_id),
                plan_id=None
            )
            medication_details.append(detail)
        i += 1

    # 处理检查明细
    check_details = []
    i = 0
    while f'check_item_id_{i}' in request.form:
        item_id = request.form.get(f'check_item_id_{i}')
        if item_id:
            detail = CheckDetail(
                record_id=record.id if record_id else None,
                item_id=int(item_id),
                status='未检查'
            )
            check_details.append(detail)
        i += 1

    try:
        db.session.add(record)
        db.session.flush()  # 获取 record.id
        for detail in medication_details:
            detail.record_id = record.id
            db.session.add(detail)
        for detail in check_details:
            detail.record_id = record.id
            db.session.add(detail)
        # 更新挂号状态为“已就诊”
        registration = Registration.query.get(record.registration_id)
        if registration:
            registration.visit_status = '已就诊'
        db.session.commit()
        flash('诊疗记录保存成功！')
        return redirect(url_for('medicalrecord.medicalrecord_list'))
    except Exception as e:
        db.session.rollback()
        return f"保存失败: {str(e)}", 500