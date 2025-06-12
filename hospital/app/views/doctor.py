from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.views.decorators import role_required
from app.models import Doctor, db, User
from app.forms import DoctorForm, DoctorUserForm
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, distinct
# doctor.py 是系统中医生信息管理的后台控制中心，仅供管理员使用，负责医生的增删改查以及为医生创建登录账号。
# url_prefix='/doctor': 此蓝图中定义的所有路由都会自动加上 '/doctor' 前缀
doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/list') # URL: /doctor/list (默认支持 GET 请求)
@role_required('admin') # 权限：只有 'admin' 角色的用户可以访问
@login_required # 权限：用户必须已登录
def doctor_list():
    # 获取查询参数
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    title = request.args.get('title', '').strip()
    status = request.args.get('status', '').strip()

    # 构建基础查询
    query = Doctor.query

    # 应用搜索条件
    if search:
        if search.isdigit():
            # 如果是数字，搜索ID
            query = query.filter(Doctor.doctor_id == int(search))
        else:
            # 否则搜索姓名
            query = query.filter(Doctor.name.like(f'%{search}%'))

    # 应用筛选条件
    if department:
        query = query.filter(Doctor.department == department)
    if title:
        query = query.filter(Doctor.title == title)
    if status:
        query = query.filter(Doctor.status == status)

    # 获取所有医生
    doctors = query.all()

    # 获取所有科室选项（用于下拉菜单）
    departments = db.session.query(Doctor.department)\
        .filter(Doctor.department.isnot(None))\
        .filter(Doctor.department != '')\
        .distinct()\
        .order_by(Doctor.department)\
        .all()
    departments = [dept[0] for dept in departments]

    # 获取所有职称选项（用于下拉菜单）
    titles = db.session.query(Doctor.title)\
        .filter(Doctor.title.isnot(None))\
        .filter(Doctor.title != '')\
        .distinct()\
        .order_by(Doctor.title)\
        .all()
    titles = [title[0] for title in titles]

    # 打印调试信息
    print("Departments:", departments)
    print("Titles:", titles)

    return render_template('doctor_list.html', 
                         doctors=doctors,
                         departments=departments,
                         titles=titles)

@doctor_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_doctor():
    form = DoctorForm()
    if form.validate_on_submit():
        # 按手机号检查是否已存在
        existing = Doctor.query.filter_by(phone=form.phone.data).first()
        if existing:
            flash('该医生已存在，请勿重复添加')
            return render_template('doctor_form.html', form=form, action='add')

        # 如果没有重复，正常添加
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