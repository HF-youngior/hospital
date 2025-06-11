import re

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import text

from app.views.decorators import role_required
from app.models import Schedule, Doctor, db
from app.forms import ScheduleForm

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
    form = ScheduleForm()
    doctors = Doctor.query.filter_by(status='在职').all()
    form.doctor_id.choices = [(d.doctor_id, f"{d.name} ({d.department})") for d in doctors]

    if form.validate_on_submit():
        # 提取表单数据
        doctor_id = form.doctor_id.data
        date = form.date.data
        time_slot = form.time_slot.data
        room_address = form.room_address.data
        reg_fee = form.reg_fee.data
        total_slots = form.total_slots.data
        remain_slots = total_slots  # 通常初始剩余数等于总数

        # 用原生SQL插入，避免 OUTPUT 触发器冲突
        insert_sql = text("""
            INSERT INTO Schedule (doctor_id, date, time_slot, room_address, reg_fee, total_slots, remain_slots)
            VALUES (:doctor_id, :date, :time_slot, :room_address, :reg_fee, :total_slots, :remain_slots)
        """)

        try:
            # 使用engine连接，自动commit事务
            with db.engine.begin() as conn:
                conn.execute(insert_sql, {
                    'doctor_id': doctor_id,
                    'date': date,
                    'time_slot': time_slot,
                    'room_address': room_address,
                    'reg_fee': reg_fee,
                    'total_slots': total_slots,
                    'remain_slots': remain_slots
                })

            flash('排班添加成功！')
            return redirect(url_for('schedule.schedule_list'))

        except Exception as e:
            # 插入失败，回滚并反馈错误
            flash(f'排班添加失败，数据库错误：{str(e)}', 'error')
            return render_template('schedule_form.html', form=form, action='add')

    # GET请求或者表单验证失败，显示添加表单
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