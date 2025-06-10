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
    # 验证医生是否有权限为该挂号看病
    if current_user.role == 'doctor' and registration.schedule.doctor_id != current_user.doctor.doctor_id:
        flash('您无权为该患者看病')
        return redirect(url_for('medicalrecord.medicalrecord_list'))
    patient_id = registration.patient_id
    drugs = Drug.query.all()
    check_items = CheckItem.query.all()
    record = MedicalRecord.query.filter_by(registration_id=registration_id).first()
    return render_template('medicalrecord.html', record=record, patient_id=patient_id, registration_id=registration_id,
                           drugs=drugs, check_items=check_items)


@medicalrecord.route('/medicalrecord/save', methods=['POST'])
@role_required('doctor')
@login_required
def save():
    registration_id = request.form.get('registration_id')
    if not registration_id:
        flash('挂号ID不能为空')
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    # 验证挂号记录
    registration = Registration.query.get_or_404(int(registration_id))
    if current_user.role == 'doctor' and registration.schedule.doctor_id != current_user.doctor.doctor_id:
        flash('您无权为该患者保存诊疗记录')
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    # 获取或创建诊疗记录
    record_id = request.form.get('record_id')
    if record_id:
        record = MedicalRecord.query.get_or_404(record_id)
    else:
        record = MedicalRecord()

    # 更新诊疗记录
    record.registration_id = int(registration_id)
    record.chief_complaint = request.form.get('chief_complaint')
    record.present_illness = request.form.get('present_illness')
    record.past_history = request.form.get('past_history')
    record.allergy_history = request.form.get('allergy_history')
    record.physical_exam = request.form.get('physical_exam')
    record.diagnosis = request.form.get('diagnosis')
    record.suggestion = request.form.get('suggestion')
    record.visit_time = datetime.now()  # 添加就诊时间

    # 处理用药明细
    medication_details = []
    i = 0
    while f'medication_drug_id_{i}' in request.form:
        drug_id = request.form.get(f'medication_drug_id_{i}')
        if drug_id:
            detail = MedicationDetail(
                registration_id=int(registration_id),  # 修正为 registration_id
                drug_id=int(drug_id)
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
                registration_id=int(registration_id),  # 修正为 registration_id
                item_id=int(item_id)
            )
            check_details.append(detail)
        i += 1

    try:
        db.session.add(record)
        # 删除旧的用药和检查记录
        MedicationDetail.query.filter_by(registration_id=registration_id).delete()
        CheckDetail.query.filter_by(registration_id=registration_id).delete()
        # 添加新的用药和检查记录
        for detail in medication_details:
            db.session.add(detail)
        for detail in check_details:
            db.session.add(detail)
        # 更新挂号状态为“已就诊”
        registration.visit_status = '已就诊'
        db.session.commit()
        flash('诊疗记录保存成功！')
        return redirect(url_for('medicalrecord.medicalrecord_list'))
    except Exception as e:
        db.session.rollback()
        flash(f'保存失败: {str(e)}')
        return redirect(url_for('medicalrecord.consult', registration_id=registration_id))