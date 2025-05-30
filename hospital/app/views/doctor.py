from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.views.decorators import role_required
from app.models import Doctor, db, User
from app.forms import DoctorForm, DoctorUserForm
from werkzeug.security import generate_password_hash

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/list')
@role_required('admin')
@login_required
def doctor_list():
    doctors = Doctor.query.all()
    return render_template('doctor_list.html', doctors=doctors)

@doctor_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_doctor():
    form = DoctorForm()
    if form.validate_on_submit():
        doctor = Doctor(
            name=form.name.data,
            gender=form.gender.data,
            title=form.title.data,
            department=form.department.data,
            phone=form.phone.data,
            status=form.status.data
        )
        db.session.add(doctor)
        db.session.commit()
        flash('医生添加成功！')
        return redirect(url_for('doctor.doctor_list'))
    return render_template('doctor_form.html', form=form, action='add')

@doctor_bp.route('/edit/<int:doctor_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorForm(obj=doctor)
    if form.validate_on_submit():
        doctor.name = form.name.data
        doctor.gender = form.gender.data
        doctor.title = form.title.data
        doctor.department = form.department.data
        doctor.phone = form.phone.data
        doctor.status = form.status.data
        db.session.commit()
        flash('医生信息已更新！')
        return redirect(url_for('doctor.doctor_list'))
    return render_template('doctor_form.html', form=form, action='edit')

@doctor_bp.route('/delete/<int:doctor_id>', methods=['POST'])
@role_required('admin')
@login_required
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    flash('医生已删除！')
    return redirect(url_for('doctor.doctor_list'))

@doctor_bp.route('/create_account/<int:doctor_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def create_doctor_account(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    form = DoctorUserForm(obj=doctor)  # 预填充医生信息
    
    if form.validate_on_submit():
        # 检查用户名是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在')
            return render_template('doctor_user_form.html', form=form, doctor=doctor)
        
        # 创建医生用户账号
        user = User(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data, method='pbkdf2:sha256'),
            role='doctor'  # 设置为医生角色
        )
        db.session.add(user)
        db.session.commit()
        
        # 关联医生和用户账号
        doctor.user_id = user.id
        db.session.commit()
        
        flash(f'医生账号"{form.username.data}"已创建并关联医生信息')
        return redirect(url_for('doctor.doctor_list'))
        
    return render_template('doctor_user_form.html', form=form, doctor=doctor) 