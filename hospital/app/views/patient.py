from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required

from app.models import Patient, Registration, MedicalRecord, MedicationDetail, CheckDetail, Payment, db,User

from app.forms import PatientForm
from sqlalchemy import desc
patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/list')
@role_required('admin')
@login_required
def patient_list():
    # 获取搜索参数
    search = request.args.get('search', '').strip()
    id_card = request.args.get('id_card', '').strip()
    insurance_card = request.args.get('insurance_card', '').strip()

    # 构建查询
    query = Patient.query

    # 应用搜索条件
    if search:
        if search.isdigit():
            # 如果是数字，尝试按ID搜索
            query = query.filter(Patient.patient_id == int(search))
        else:
            # 否则按姓名搜索
            query = query.filter(Patient.name.contains(search))
    
    if id_card:
        query = query.filter(Patient.id_card.contains(id_card))
    
    if insurance_card:
        query = query.filter(Patient.insurance_card.contains(insurance_card))

    # 执行查询
    patients = query.all()
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
        # 新增：同步User表
        user = User.query.filter_by(id_card=patient.id_card).first()
        if user:
            user.patient_id = patient.patient_id
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
        # 新增：同步User表
        user = User.query.filter_by(id_card=patient.id_card).first()
        if user:
            user.patient_id = patient.patient_id
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
    if not current_user.patient_id:
        flash('您的账号未关联患者信息')
        return redirect(url_for('main.index'))

    # 只显示未取消的挂号记录
    registrations = Registration.query.filter_by(
        patient_id=current_user.patient_id
    ).filter(Registration.visit_status != '已取消').order_by(desc(Registration.reg_time)).all()

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

    medical_record = MedicalRecord.query.filter_by(registration_id=registration_id).first()
    medications = MedicationDetail.query.filter_by(registration_id=registration_id).all()
    checks = CheckDetail.query.filter_by(registration_id=registration_id).all()
    payments = Payment.query.filter_by(registration_id=registration_id).all()

    return render_template('record_detail.html',
                           registration=registration,
                           medical_record=medical_record,
                           medications=medications,
                           checks=checks,
                           payments=payments)