from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import Patient, db, User
from app.forms import PatientForm

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
    registrations = []
    # 如果用户已关联患者信息，查询挂号记录
    if current_user.patient_id:
        # 这里可以查询患者的挂号记录，暂时为空列表
        # 实际开发时，需要增加Registration模型的查询
        # registrations = Registration.query.filter_by(patient_id=current_user.patient_id).all()
        pass
        
    return render_template('patient_profile.html', user=current_user, registrations=registrations) 