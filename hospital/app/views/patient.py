from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import Patient, Registration, MedicalRecord, MedicationDetail, CheckDetail, Payment, db
from app.forms import PatientForm
from sqlalchemy import desc
patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/list')
@role_required('admin')
@login_required
def patient_list():
    patients = Patient.query.all()
    return render_template('patient_list.html', patients=patients)

@patient_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_patient():
    form = PatientForm()
    if form.validate_on_submit():
        if Patient.query.filter_by(id_card=form.id_card.data).first():
            flash('该身份证号已存在！')
            return render_template('patient_form.html', form=form, action='add')
        patient = Patient(
            name=form.name.data,
            gender=form.gender.data,
            birth_date=form.birth_date.data,
            contact=form.contact.data,
            id_card=form.id_card.data,
            insurance_card=form.insurance_card.data,
            insurance_balance=form.insurance_balance.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('患者添加成功！')
        return redirect(url_for('patient.patient_list'))
    return render_template('patient_form.html', form=form, action='add')

@patient_bp.route('/edit/<int:patient_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        patient.name = form.name.data
        patient.gender = form.gender.data
        patient.birth_date = form.birth_date.data
        patient.contact = form.contact.data
        patient.id_card = form.id_card.data
        patient.insurance_card = form.insurance_card.data
        patient.insurance_balance = form.insurance_balance.data
        db.session.commit()
        flash('患者信息已更新！')
        return redirect(url_for('patient.patient_list'))
    return render_template('patient_form.html', form=form, action='edit')

@patient_bp.route('/delete/<int:patient_id>', methods=['POST'])
@role_required('admin')
@login_required
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash('患者已删除！')
    return redirect(url_for('patient.patient_list'))

@patient_bp.route('/profile')
@login_required
def patient_profile():
    """患者个人中心页面"""
    registrations = []
    # 如果用户已关联患者信息，查询挂号记录
    if not current_user.patient_id:
            flash('患者已删除！')
            return redirect(url_for('patient.patient_list'))
        # 这里可以查询患者的挂号记录，暂时为空列表
        # 实际开发时，需要增加Registration模型的查询
        # registrations = Registration.query.filter_by(patient_id=current_user.patient_id).all()
    registrations = Registration.query.filter_by(
        patient_id=current_user.patient_id
    ).order_by(desc(Registration.reg_time)).all()

    return render_template('patient_profile.html', user=current_user, registrations=registrations)


@patient_bp.route('/record/<int:registration_id>')
@login_required
@role_required('patient')
def view_record(registration_id):
    """查看单次就诊详情"""
    registration = Registration.query.get_or_404(registration_id)
    if registration.patient_id != current_user.patient_id:
        flash('您无权查看此记录')
        return redirect(url_for('patient.patient_profile'))

    # 查询诊疗记录
    medical_record = MedicalRecord.query.filter_by(registration_id=registration_id).first()

    # 查询用药和检查详情
    medications = MedicationDetail.query.filter_by(registration_id=registration_id).all()
    checks = CheckDetail.query.filter_by(registration_id=registration_id).all()

    # 查询支付记录
    payments = Payment.query.filter_by(registration_id=registration_id).all()

    # 为用药和检查添加支付状态
    for med in medications:
        med.is_paid = any(p.fee_type == '药品费' and p.pay_status == '已支付' for p in payments)
    for check in checks:
        check.is_paid = any(p.fee_type == '检查费' and p.pay_status == '已支付' for p in payments)

    return render_template('record_detail.html',
                           registration=registration,
                           medical_record=medical_record,
                           medications=medications,
                           checks=checks,
                           payments=payments)