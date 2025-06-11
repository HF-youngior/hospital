from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import Schedule, Registration, Patient, Doctor, Payment, MedicalRecord, Drug, CheckItem, MedicationDetail, CheckDetail, db
from datetime import datetime,  timedelta # 确保导入 timedelta, 如果不直接比较时间，可以移除 time
from datetime import date as py_date
from flask import abort  # 确保导入 abort
from flask import current_app

from sqlalchemy import desc,func

# 创建一个名为 'registration' 的蓝本，并指定 URL 前缀
registration_bp = Blueprint('registration', __name__, url_prefix='/registration')

# --- 辅助函数：中文星期 ---
def get_weekday_zh(target_date):
    """将日期对象转换为中文星期字符串。"""
    week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return week_days[target_date.weekday()] # weekday() 返回0代表周一，6代表周日
PREDEFINED_TIME_SLOTS_FOR_CALENDAR = [
    {"name": "上午", "display_text": "上午 (8:00-12:00)", "order": 1},
    {"name": "下午", "display_text": "下午 (14:00-17:30)", "order": 2},
    {"name": "晚上", "display_text": "晚上 (18:00-20:00)", "order": 3},
]
# 按显示顺序排序，以确保模板中一致的渲染顺序
PREDEFINED_TIME_SLOTS_FOR_CALENDAR.sort(key=lambda x: x.get('order', 0))


#一进来先看这个视图
@registration_bp.route('/list')
@login_required
def registration_list():
    """
        显示挂号列表视图。
        - 管理员(admin): 查看所有挂号记录。
        - 医生(doctor): 查看与自己相关的挂号记录 (通过其 User ID 关联到 Doctor ID，再关联到 Schedule)。
        - 患者(patient): 查看自己的挂号记录 (通过 current_user.patient_id)。
        所有记录按挂号时间(reg_time)降序排列。
    """
    print('进入registration_list')
    if current_user.role == 'admin':
        # 管理员获取所有挂号记录，并按挂号时间倒序排序
        registrations = Registration.query.order_by(desc(Registration.reg_time)).all()
    elif current_user.role == 'doctor':
        # 医生用户，首先获取其对应的 Doctor 实体信息
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            # 如果找到了医生信息，则查询与该医生相关的排班(Schedule)的挂号记录
            registrations = Registration.query.join(Schedule).filter(
                Schedule.doctor_id == doctor.doctor_id
            ).order_by(desc(Registration.reg_time)).all()
        else:
            registrations = []
    else:# 患者用户
        if current_user.patient_id:
            registrations = Registration.query.filter_by(
                patient_id=current_user.patient_id
            ).order_by(desc(Registration.reg_time)).all()
        else:
            registrations = []
    for reg in registrations:
        print(f"Registration ID: {reg.registration_id}, Schedule ID: {reg.schedule_id}, Schedule: {reg.schedule}")
    return render_template('registration_list.html', registrations=registrations, current_date=datetime.now().date())

# 这是挂号入口111
@registration_bp.route('/select_department', methods=['GET'])
@login_required
def select_department_page():
    """
    显示科室选择页面，供用户选择要挂号的科室。
    """
    print('进入select_department_page')
    try:
        # 从 Doctor 模型中获取所有不重复的科室名称
        # 假设 Doctor 模型有一个 'department' 字段存储科室名称
        departments_query = db.session.query(Doctor.department).distinct().order_by(Doctor.department).all()

        # 将查询结果 (元组列表) 转换为字符串列表，并过滤掉可能存在的 None 或空字符串
        departments = [dept[0] for dept in departments_query if dept[0] and dept[0].strip()]

        if not departments:
            flash("目前系统中没有配置科室信息，无法进行挂号。", "warning")
            # 可以重定向到首页或显示一个更友好的无科室页面
            return redirect(url_for('main.index'))  # 假设 'main.index' 是您的主页路由

    except Exception as e:
        current_app.logger.error(f"获取科室列表失败: {str(e)}")
        flash("获取科室列表失败，请稍后重试或联系管理员。", "danger")
        departments = []  # 发生错误时返回空列表

    return render_template('select_department.html', departments=departments)


@registration_bp.route('/make/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
@role_required('patient', 'admin')
def make_registration(schedule_id):
    """
    处理针对特定排班ID (schedule_id) 的挂号请求。
    - GET 请求:
        - 如果是患者用户，通常直接进入POST逻辑（因为患者是为自己挂号）。
        - 如果是管理员用户，显示一个选择患者的界面，让管理员可以为系统内的任一患者挂号。
    - POST 请求: 执行实际的挂号创建、费用计算、扣款等操作。
    """
    print('进入make_registration111111')
    schedule = Schedule.query.get_or_404(schedule_id)
    # 检查排班有效性
    if schedule.remain_slots <= 0:
        flash('对不起，该时段已无余号')
        # return redirect(url_for('registration.available_schedules'))
        return "功能开发中，暂时重定向到这里。"
    if schedule.date < datetime.now().date():   # 比较日期，确保不是过去的排班
        flash('对不起，该排班日期已过')
        # return redirect(url_for('registration.available_schedules'))
        return "功能开发中，暂时重定向到这里。"

    patient_id = None

    if current_user.role == 'patient':
        if current_user.patient_id:
            patient_id = current_user.patient_id
        else:
            flash('您的账号未关联患者信息，请先完善个人信息')
            return redirect(url_for('patient.patient_profile'))
    elif current_user.role == 'admin':
        if request.method == 'POST':
            # 管理员通过表单提交为指定患者挂号
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
            # return redirect(url_for('registration.available_schedules'))
            return "功能开发中，暂时重定向到这里。"

        patient = Patient.query.get(patient_id)
        reg_fee = schedule.reg_fee
        insurance_rate = 0.8
        insurance_amount = reg_fee * insurance_rate
        self_pay_amount = reg_fee * (1 - insurance_rate)

        if patient.insurance_balance < insurance_amount:
            flash('医保余额不足以支付挂号费！')
            # return redirect(url_for('registration.available_schedules'))
            return "功能开发中，暂时重定向到这里。"

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
    # return redirect(url_for('registration.available_schedules'))
    return "功能开发中，暂时重定向到这里。"


##新加入
@registration_bp.route('/departments/<string:department_name>/doctors', methods=['GET'])
@login_required # 如果此页面需要登录才能访问
def list_doctors_in_department(department_name):
    """
    显示指定科室下的医生列表。
    """
    # 模拟从数据库根据 department_name 获取医生列表
    # .get(department_name) 会在科室名称不存在时返回 None
    print('进入list_doctors_in_department')
    department_exists = db.session.query(
        Doctor.query.filter_by(department=department_name).exists()
    ).scalar()

    if not department_exists:
        flash(f"未找到名为 '{department_name}' 的科室或该科室下无医生。", "warning")

    # 2. 查询该科室下的所有医生
    doctors_list = Doctor.query.filter_by(department=department_name).all()

    return render_template(
        'list_doctors.html',
        department_name=department_name,
        doctors=doctors_list  # 直接传递查询结果（可能是空列表）
    )

###挂号22222
@registration_bp.route('/departments/<string:department_name>/schedule_calendar', methods=['GET'])
@login_required
def department_schedule_calendar(department_name):
    """
    显示指定科室未来几天的聚合排班日历表。
    """
    # 1. 验证 department_name
    # 由于 Schedule 表中没有 department 字段，我们需要通过 Doctor 表来找到属于该科室的医生，
    # 然后再用这些医生的 ID 去查询 Schedule 表。

    # 找到该科室下的所有医生 ID
    print('进入department_schedule_calendar')
    doctors_in_dept = Doctor.query.filter_by(department=department_name).all()
    if not doctors_in_dept:
        flash(f"未找到名为 '{department_name}' 的科室，或该科室下无医生。", "warning")
        return redirect(url_for('registration.list_departments')) # 假设这是您的科室列表路由  2.1入口

    doctor_ids_in_dept = [doc.doctor_id for doc in doctors_in_dept]

    # 2. 定义日期范围
    num_days_to_display = 7
    today = py_date.today() # 使用重命名的 py_date
    dates_to_display = []
    for i in range(num_days_to_display):
        current_display_date = today + timedelta(days=i)
        dates_to_display.append({
            "date_obj": current_display_date,
            "short_str": current_display_date.strftime("%m/%d"),
            "weekday_str": "今天" if i == 0 else get_weekday_zh(current_display_date)
        })

    # 3. 获取相关排班数据
    start_date_range = dates_to_display[0]["date_obj"]
    end_date_range = dates_to_display[-1]["date_obj"]

    all_schedules_raw = Schedule.query.filter(
        Schedule.doctor_id.in_(doctor_ids_in_dept), # 使用该科室医生的 ID 列表
        Schedule.date.between(start_date_range, end_date_range), # 使用 Schedule.date
        Schedule.remain_slots > 0
    ).order_by(Schedule.date, Schedule.doctor_id) \
     .all() # Doctor 信息会通过 lazy='joined' 自动加载

    # 4. 构建用于模板的矩阵
    schedule_matrix = {
        dt_info["date_obj"].isoformat(): {
            ts_info["name"]: [] for ts_info in PREDEFINED_TIME_SLOTS_FOR_CALENDAR
        }
        for dt_info in dates_to_display
    }

    for sch in all_schedules_raw:
        sch_date_iso = sch.date.isoformat() # 使用 Schedule.date
        time_slot_key = sch.time_slot       # 使用 Schedule.time_slot

        if sch_date_iso in schedule_matrix and time_slot_key in schedule_matrix[sch_date_iso]:
            schedule_matrix[sch_date_iso][time_slot_key].append(sch)
        # else:
        #     current_app.logger.warn(
        #         f"排班ID {sch.schedule_id} (日期 {sch_date_iso}, 时段 '{time_slot_key}') "
        #         f"未能匹配到日历的预定义时段中。请检查 PREDEFINED_TIME_SLOTS_FOR_CALENDAR "
        #         f"和数据库中 Schedule.time_slot 的值，以及日期范围。"
        #     )

    return render_template(
        'department_schedule_calendar.html',
        department_name=department_name,
        dates_header=dates_to_display,
        time_slots_header=PREDEFINED_TIME_SLOTS_FOR_CALENDAR,
        schedule_matrix=schedule_matrix
    )

###2.1 跳转到科室列表路由url_for('registration.list_departments'))
@registration_bp.route('/departments', methods=['GET'])
@login_required # 通常选择科室也需要登录
# @role_required('patient', 'admin') # 根据需求，患者和管理员通常都可以访问
def list_departments():
    """
    显示所有可供选择的科室列表。
    科室信息来源于 Doctor 表中的 department 字段。
    """
    print('进入list_departments')
    try:
        # 查询 Doctor 表中所有不重复的科室名称
        # Doctor.department 是一个字符串字段
        # distinct(Doctor.department) 会选取不重复的科室名
        # .all() 返回结果列表，每个元素是一个元组，例如 [('内科',), ('外科',), ...]
        department_tuples = db.session.query(Doctor.department).filter(Doctor.department.isnot(None), Doctor.department != '').distinct().order_by(Doctor.department).all()

        # 将元组列表转换为字符串列表
        departments = [dept_tuple[0] for dept_tuple in department_tuples if dept_tuple[0]] # 确保科室名不为空

        if not departments:
            flash('目前系统中没有可供选择的科室信息。', 'info')
            # 可以重定向到首页或其他地方
            return redirect(url_for('main.index')) # 假设你有一个名为 'main.index' 的主页路由

    except Exception as e:
        flash(f'加载科室列表失败，发生错误：{str(e)}', 'danger')
        # 记录日志
        # current_app.logger.error(f"加载科室列表失败: {str(e)}", exc_info=True)
        departments = [] # 出错时返回空列表，模板可以处理这种情况
        # 或者重定向到错误页面或首页
        return redirect(url_for('main.index'))


    # 渲染选择科室的模板，并传递科室列表
    return render_template('select_department.html', departments=departments)
###2.2进入日历挂号后，选择医生，跳转至此
@registration_bp.route('/schedules/<int:schedule_id>/create_appointment', methods=['GET', 'POST'])  # <--- 修改1: 允许 POST
@login_required
def create_appointment_page(schedule_id):
    print('进入create_appointment_page')
    schedule_item = db.session.get(Schedule, schedule_id)  # 使用 db.session.get 更好
    if not schedule_item:
        abort(404)

    current_patient = None
    if hasattr(current_user, 'patient') and current_user.patient:
        current_patient = current_user.patient

    if not current_patient:
        flash('请先在个人中心绑定或完善您的就诊人信息才能挂号。', 'danger')
        profile_url = url_for('patient.patient_profile', _external=True,
                              _scheme=current_app.config.get('PREFERRED_URL_SCHEME', 'http'))
        return redirect(profile_url)

    # --- 修改2: 添加 POST 请求处理逻辑 ---
    if request.method == 'POST':
        # 再次检查号源 (重要！因为从GET到POST之间可能有变化)
        # 重新从数据库获取最新的 schedule_item 状态，以避免竞态条件
        # 或者使用数据库锁，这里简化处理，直接用之前的 schedule_item，但最好重新获取
        refreshed_schedule_item = db.session.get(Schedule, schedule_id)
        if not refreshed_schedule_item or refreshed_schedule_item.remain_slots <= 0:
            flash('抱歉，您操作期间号源已无或排班信息有变，请重新选择。', 'warning')
            return redirect(url_for('.department_schedule_calendar', department_name=schedule_item.doctor.department))

        # 检查患者是否已在该时段预约了该医生
        existing_registration = Registration.query.filter(
            Registration.patient_id == current_patient.patient_id,
            Registration.schedule_id == refreshed_schedule_item.schedule_id,  # 使用刷新后的
            Registration.visit_status != '已取消'
        ).first()

        if existing_registration:
            flash(
                f'您已预约过 {refreshed_schedule_item.doctor.name}医生 在 {refreshed_schedule_item.date.strftime("%Y-%m-%d")} {refreshed_schedule_item.time_slot} 的号，请勿重复挂号。',
                'warning')
            return redirect(url_for('.create_appointment_page', schedule_id=schedule_id))

        try:
            # 确保在事务中操作
            if refreshed_schedule_item.remain_slots > 0:
                refreshed_schedule_item.remain_slots -= 1  # 更新刷新后的对象

                new_registration = Registration(
                    patient_id=current_patient.patient_id,
                    schedule_id=refreshed_schedule_item.schedule_id,
                    reg_time=datetime.utcnow(),
                    visit_status='待就诊',
                )
                db.session.add(new_registration)
                # refreshed_schedule_item 是受 SQLAlchemy 管理的对象，其属性修改会被追踪
                # db.session.add(refreshed_schedule_item) # 可以不显式 add，但为了清晰也可以加上
                db.session.commit()

                flash(
                    f'恭喜您，成功为患者【{current_patient.name}】预约 {refreshed_schedule_item.doctor.name} 医生！详细信息如下：',
                    'success')

                # --- 这是 "第五步 B" 的核心修改 ---
                return redirect(url_for('.registration_success_page', registration_id=new_registration.registration_id))
                # --- 核心修改结束 ---
            else:
                # 理论上在上面的 refreshed_schedule_item.remain_slots <= 0 已经捕获
                db.session.rollback()  # 以防万一
                flash('非常抱歉，号源已被抢完，请重新选择。', 'danger')
                return redirect(
                    url_for('.department_schedule_calendar', department_name=refreshed_schedule_item.doctor.department))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"创建挂号记录失败 for schedule_id {schedule_id}, patient_id {current_patient.patient_id}: {str(e)}")
            flash('挂号失败，发生内部错误，请稍后再试。', 'danger')
            return redirect(url_for('.create_appointment_page', schedule_id=schedule_id))
        # --- POST 请求处理结束 ---

    # --- 处理 GET 请求 (显示页面，与您之前的逻辑类似) ---
    if schedule_item.remain_slots <= 0:  # GET 时也检查一次
        flash('抱歉，该时段号源已满，请选择其他时段或医生。', 'warning')
        return redirect(url_for('.department_schedule_calendar', department_name=schedule_item.doctor.department))

    context = {
        'schedule': schedule_item,
        'patient': current_patient,
        'weekday_str': get_weekday_zh(schedule_item.date),  # 添加 weekday_str
        'py_date': py_date  # 添加 py_date (如果模板需要)
    }
    return render_template('create_appointment.html', **context)


@registration_bp.route('/registration/<int:registration_id>/success')
@login_required
def registration_success_page(registration_id):
    """
    显示挂号成功的详情页面。
    """
    registration_record = db.session.get(Registration, registration_id)  # 使用 db.session.get 更佳
    if not registration_record:
        abort(404)  # 如果找不到该挂号记录

    # --- 权限检查：确保当前用户有权查看此挂号记录 ---
    # 1. 获取当前用户的 patient_id
    current_user_patient_id = None
    if current_user.is_authenticated and hasattr(current_user, 'patient') and current_user.patient:
        current_user_patient_id = current_user.patient.patient_id

    # 2. 检查挂号记录中的 patient_id 是否与当前用户的 patient_id 匹配
    #    或者，如果当前用户是管理员等角色，也允许查看 (这里简化，只检查患者本人)
    if registration_record.patient_id != current_user_patient_id:
        # 如果用户不是此挂号记录的患者，并且不是管理员 (未来可以添加管理员逻辑)
        flash("您无权查看此挂号详情。", "warning")
        return redirect(url_for('main.index'))  # 或其他合适的页面

    # 获取挂号记录关联的排班和医生信息，以及患者信息
    # Registration 模型中 lazy='joined' 会自动加载 patient 和 schedule
    # schedule 又关联了 doctor

    context = {
        'registration': registration_record,
        'schedule': registration_record.schedule,  # 可以直接从 registration_record.schedule 获取
        'doctor': registration_record.schedule.doctor,  # 再从 schedule 获取 doctor
        'patient': registration_record.patient,  # 直接从 registration_record.patient 获取
        'weekday_str': get_weekday_zh(registration_record.schedule.date),
        'py_date': py_date  # 为了页脚的年份 (如果模板需要)
    }

    return render_template('registration_success.html', **context)






#取消
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
# 支付药
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
# 支付检查
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
#看支付情况
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