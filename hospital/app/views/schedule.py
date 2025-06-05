from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import Schedule, Doctor, db
from app.forms import ScheduleForm
from datetime import datetime

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')

@schedule_bp.route('/list')
@login_required
@role_required('admin', 'doctor')
def schedule_list():
    """排班列表"""
    if current_user.role == 'admin':
        # 管理员可以看到所有排班
        schedules = Schedule.query.all()
    else:
        # 医生只能看到自己的排班
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            schedules = Schedule.query.filter_by(doctor_id=doctor.doctor_id).all()
        else:
            schedules = []
    
    return render_template('schedule_list.html', schedules=schedules)

@schedule_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_schedule():
    """添加排班"""
    form = ScheduleForm()
    
    # 获取所有医生列表作为下拉选项
    doctors = Doctor.query.filter_by(status='在职').all()
    form.doctor_id.choices = [(d.doctor_id, f"{d.name} ({d.department})") for d in doctors]
    
    if form.validate_on_submit():
        # 自动填充科室信息
        doctor = Doctor.query.get(form.doctor_id.data)
        
        schedule = Schedule(
            doctor_id=form.doctor_id.data,
            date=form.date.data,
            time_slot=form.time_slot.data,
            # department=doctor.department,  # 从医生信息获取科室
            room_address=form.room_address.data,
            reg_fee=form.reg_fee.data,
            total_slots=form.total_slots.data,
            remain_slots=form.total_slots.data  # 初始时剩余号源等于总号源
        )
        db.session.add(schedule)
        db.session.commit()
        flash('排班添加成功！')
        return redirect(url_for('schedule.schedule_list'))
    
    return render_template('schedule_form.html', form=form, action='add')

@schedule_bp.route('/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_schedule(schedule_id):
    """编辑排班"""
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # 获取所有医生列表作为下拉选项
    doctors = Doctor.query.filter_by(status='在职').all()
    
    form = ScheduleForm(obj=schedule)
    form.doctor_id.choices = [(d.doctor_id, f"{d.name} ({d.department})") for d in doctors]
    
    if form.validate_on_submit():
        # 获取医生信息
        doctor = Doctor.query.get(form.doctor_id.data)
        
        schedule.doctor_id = form.doctor_id.data
        schedule.date = form.date.data
        schedule.time_slot = form.time_slot.data
        schedule.department = doctor.department  # 从医生信息获取科室
        schedule.room_address = form.room_address.data
        schedule.reg_fee = form.reg_fee.data
        schedule.total_slots = form.total_slots.data
        
        # 如果修改总号源数，同步修改剩余号源数
        if schedule.remain_slots > form.total_slots.data:
            schedule.remain_slots = form.total_slots.data
        
        db.session.commit()
        flash('排班信息已更新！')
        return redirect(url_for('schedule.schedule_list'))
    
    return render_template('schedule_form.html', form=form, action='edit')

@schedule_bp.route('/delete/<int:schedule_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_schedule(schedule_id):
    """删除排班"""
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    flash('排班已删除！')
    return redirect(url_for('schedule.schedule_list')) 