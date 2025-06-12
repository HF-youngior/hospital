
from app import create_app, db
from app.models import User, Patient, Doctor, Schedule, Registration, Payment, MedicalRecord, MedicationDetail, \
    CheckDetail, Drug, CheckItem
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from sqlalchemy import text

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # 创建管理员账号
    admin = User(
        username='admin',
        password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
        role='admin'
    )
    db.session.add(admin)
    db.session.flush()

    # 创建多个医生信息
    doctors = [
        {
            'name': '金珞辰',
            'gender': '女',
            'title': '主任医师',
            'department': '外科',
            'phone': '13032303383',
            'status': '在职'
        },
        {
            'name': '李明辉',
            'gender': '男',
            'title': '副主任医师',
            'department': '内科',
            'phone': '13032303384',
            'status': '在职'
        },
        {
            'name': '张晓红',
            'gender': '女',
            'title': '主治医师',
            'department': '儿科',
            'phone': '13032303385',
            'status': '在职'
        }
    ]

    doctor_users = []
    for i, doc in enumerate(doctors, 1):
        doctor = Doctor(**doc)
        db.session.add(doctor)
        db.session.flush()

        doctor_user = User(
            username=f'doctor{i}',
            password_hash=generate_password_hash(f'doctor{i}123', method='pbkdf2:sha256'),
            role='doctor'
        )
        db.session.add(doctor_user)
        db.session.flush()

        doctor.user_id = doctor_user.id
        doctor_users.append(doctor_user)
        print(f"医生账号 {doctor_user.username} 已关联医生 {doctor.name} ({doctor.department})")

    # 创建多个患者信息（模拟医院登记）
    patients = [
        {
            'name': '杨雅涵',
            'gender': '女',
            'birth_date': date(2005, 6, 25),
            'contact': '13883373133',
            'id_card': '500107200506251646',
            'insurance_card': '061371137',
            'insurance_balance': 10000.0
        },
        {
            'name': '王强',
            'gender': '男',
            'birth_date': date(1990, 3, 15),
            'contact': '13883373134',
            'id_card': '500107199003151234',
            'insurance_card': '061371138',
            'insurance_balance': 8000.0
        },
        {
            'name': '刘芳',
            'gender': '女',
            'birth_date': date(1985, 8, 20),
            'contact': '13883373135',
            'id_card': '500107198508201345',
            'insurance_card': '061371139',
            'insurance_balance': 12000.0
        }
    ]

    patient_users = []
    for i, pat in enumerate(patients, 1):
        patient = Patient(**pat)
        db.session.add(patient)
        db.session.flush()

        patient_user = User(
            username=pat['name'],
            password_hash=generate_password_hash(f'patient{i}123', method='pbkdf2:sha256'),
            role='patient',
            id_card=patient.id_card,
            patient_id=patient.patient_id
        )
        db.session.add(patient_user)
        db.session.flush()

        patient_users.append(patient_user)
        print(f"患者账号 {patient_user.username} 已关联患者 {patient.name} (身份证: {patient.id_card})")

    # 创建药品
    drugs = [
        Drug(
            name='阿司匹林',
            specification='100mg*100片',
            price=25.0,
            usage='口服',
            frequency='每日一次',
            stock=100,
            remark='解热镇痛',
            status='可用',
            insurance_rate=0.8
        ),
        Drug(
            name='头孢克洛',
            specification='250mg*12粒',
            price=45.0,
            usage='口服',
            frequency='每日两次',
            stock=50,
            remark='抗生素',
            status='可用',
            insurance_rate=0.8
        )
    ]
    db.session.add_all(drugs)
    db.session.flush()

    # 创建检查项目
    check_items = [
        CheckItem(name='血常规', price=50.0, department='检验科', insurance_rate=0.8),
        CheckItem(name='胸片', price=150.0, department='放射科', insurance_rate=0.8)
    ]
    db.session.add_all(check_items)
    db.session.flush()

    # 创建排班
    schedules = [
        Schedule(
            doctor_id=doctor_users[0].doctor.doctor_id,
            date=date.today(),
            time_slot='上午',
            room_address='外科诊室101',
            reg_fee=50.0,
            total_slots=10,
            remain_slots=8
        ),
        Schedule(
            doctor_id=doctor_users[0].doctor.doctor_id,
            date=date.today(),
            time_slot='下午',
            room_address='外科诊室101',
            reg_fee=50.0,
            total_slots=10,
            remain_slots=10
        ),
        Schedule(
            doctor_id=doctor_users[1].doctor.doctor_id,
            date=date.today(),
            time_slot='上午',
            room_address='内科诊室201',
            reg_fee=40.0,
            total_slots=12,
            remain_slots=12
        ),
        Schedule(
            doctor_id=doctor_users[2].doctor.doctor_id,
            date=date.today(),
            time_slot='上午',
            room_address='儿科诊室301',
            reg_fee=45.0,
            total_slots=15,
            remain_slots=15
        )
    ]
    db.session.add_all(schedules)
    db.session.flush()

    # 创建挂号记录
    registrations = [
        Registration(
            patient_id=patient_users[0].patient_id,
            schedule_id=schedules[0].schedule_id,
            reg_time=datetime.now(),
            visit_status='待就诊'
        ),
        Registration(
            patient_id=patient_users[0].patient_id,
            schedule_id=schedules[0].schedule_id,
            reg_time=datetime.now(),
            visit_status='已取消'
        ),
        Registration(
            patient_id=patient_users[1].patient_id,
            schedule_id=schedules[2].schedule_id,
            reg_time=datetime.now(),
            visit_status='待就诊'
        ),
        Registration(
            patient_id=patient_users[2].patient_id,
            schedule_id=schedules[3].schedule_id,
            reg_time=datetime.now(),
            visit_status='待就诊'
        )
    ]
    db.session.add_all(registrations)
    db.session.flush()

    # 创建支付记录（挂号费）
    for reg in registrations:
        if reg.visit_status != '已取消':
            patient = Patient.query.get(reg.patient_id)
            reg_fee = reg.schedule.reg_fee
            insurance_rate = 0.8
            insurance_amount = reg_fee * insurance_rate
            self_pay_amount = reg_fee * (1 - insurance_rate)
            patient.insurance_balance -= insurance_amount

            payment = Payment(
                registration_id=reg.registration_id,
                fee_type='挂号费',
                insurance_amount=insurance_amount,
                self_pay_amount=self_pay_amount,
                pay_method='医保支付',
                pay_time=datetime.now(),
                pay_status='已支付'
            )
            db.session.add(payment)

    # 创建诊疗记录
    medical_record = MedicalRecord(
        registration_id=registrations[0].registration_id,
        visit_time=datetime.now(),
        chief_complaint='头痛一周',
        present_illness='间断性头痛，无明显诱因',
        past_history='无特殊病史',
        allergy_history='无',
        physical_exam='血压正常，心肺无异常',
        diagnosis='偏头痛',
        suggestion='服用阿司匹林，观察病情'
    )
    db.session.add(medical_record)
    db.session.flush()

    # 创建用药和检查明细
    medication_detail = MedicationDetail(
        registration_id=registrations[0].registration_id,
        drug_id=drugs[0].drug_id,
        quantity=1  # 新增字段
    )
    check_detail = CheckDetail(
        registration_id=registrations[0].registration_id,
        item_id=check_items[0].item_id,
        result='未完成',
        quantity=1  # 新增字段
    )
    db.session.add_all([medication_detail, check_detail])
    db.session.flush()

    # 创建药品和检查支付记录
    patient = Patient.query.get(registrations[0].patient_id)
    drug_payment = Payment(
        registration_id=registrations[0].registration_id,
        fee_type='药品费',
        insurance_amount=drugs[0].price * 0.8,
        self_pay_amount=drugs[0].price * 0.2,
        pay_method='医保支付',
        pay_time=datetime.now(),
        pay_status='已支付'
    )
    db.session.add(drug_payment)

    check_payment = Payment(
        registration_id=registrations[0].registration_id,
        fee_type='检查费',
        insurance_amount=check_items[0].price * 0.8,
        self_pay_amount=check_items[0].price * 0.2,
        pay_method='医保支付',
        pay_time=datetime.now(),
        pay_status='已支付'
    )
    db.session.add(check_payment)

    patient.insurance_balance -= (drugs[0].price * 0.8 + check_items[0].price * 0.8)

    registrations[0].visit_status = '已就诊'

    db.session.commit()
    print("数据库表已创建完成！")
    print("初始管理员账号：用户名: admin, 密码: admin123")
    print("医生账号：")
    for i in range(1, 4):
        print(f"  用户名: doctor{i}, 密码: doctor{i}123")
    print("患者账号：")
    for i, user in enumerate(patient_users, 1):
        print(f"  用户名: {user.username}, 密码: patient{i}123")

    # SQLAlchemy 的 execute 不支持 GO 语句，需要分割执行
    # 先删除触发器语句
    drop_trigger_sql = """
    IF OBJECT_ID ('trg_check_schedule_duplicate', 'TR') IS NOT NULL
        DROP TRIGGER trg_check_schedule_duplicate;
    IF OBJECT_ID ('generate_payment_after_insert_medication', 'TR') IS NOT NULL
        DROP TRIGGER generate_payment_after_insert_medication;
    IF OBJECT_ID ('generate_payment_after_insert_check', 'TR') IS NOT NULL
        DROP TRIGGER generate_payment_after_insert_check;
    """
    with db.engine.connect() as conn:
        conn.execute(text(drop_trigger_sql))
        conn.commit()

    # 创建排班冲突触发器
    create_trg_check_schedule_duplicate_sql = """
    CREATE TRIGGER trg_check_schedule_duplicate
    ON Schedule
    INSTEAD OF INSERT
    AS
    BEGIN
        -- 同一个医生同一天同一时间段，重复排班
        IF EXISTS (
            SELECT 1
            FROM Schedule s
            INNER JOIN inserted i
                ON s.doctor_id = i.doctor_id
                AND s.date = i.date
                AND s.time_slot = i.time_slot
        )
        BEGIN
            RAISERROR('排班冲突：该医生在该日期和时间段已有排班记录，不能重复添加。', 16, 1);
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- 不同医生在同一天同一时间段同一诊室，冲突
        IF EXISTS (
            SELECT 1
            FROM Schedule s
            INNER JOIN inserted i
                ON s.date = i.date
                AND s.time_slot = i.time_slot
                AND s.room_address = i.room_address
                AND s.doctor_id <> i.doctor_id
        )
        BEGIN
            RAISERROR('排班冲突：已有其他医生在相同日期、时间段和诊室排班，不能重复安排。', 16, 1);
            ROLLBACK TRANSACTION;
            RETURN;
        END
        -- 如果没有冲突，正常插入
        INSERT INTO Schedule (doctor_id, date, time_slot, room_address, reg_fee, total_slots, remain_slots)
        SELECT doctor_id, date, time_slot, room_address, reg_fee, total_slots, remain_slots
        FROM inserted;
    END;
    """
    with db.engine.connect() as conn:
        conn.execute(text(create_trg_check_schedule_duplicate_sql))
        conn.commit()

    drop_proc_sql = """
        IF OBJECT_ID('sp_GetMedicalRecordInfo', 'P') IS NOT NULL
        DROP PROCEDURE sp_GetMedicalRecordInfo;
    """
    with db.engine.connect() as conn:
        conn.execute(text(drop_proc_sql))
        conn.commit()

    create_proc_sql = """
    CREATE PROCEDURE sp_GetMedicalRecordInfo
        @registration_id INT
    AS
    BEGIN
        SET NOCOUNT ON;

        -- 查询病人信息
        SELECT 
            p.patient_id,
            p.name AS patient_name,
            p.gender,
            p.birth_date,
            p.id_card,
            p.contact,
           r.reg_time,
            d.name AS doctor_name,
            d.department,
            r.visit_status
        FROM registration r
        JOIN patient p ON r.patient_id = p.patient_id
        JOIN schedule s ON r.schedule_id = s.schedule_id
        JOIN doctor d ON s.doctor_id = d.doctor_id
        WHERE r.registration_id = @registration_id;

       -- 查询药品明细
        SELECT 
            md.detail_id,
            dr.name AS drug_name,
            dr.specification,
            dr.price,
            md.quantity,  -- 更新为使用 quantity 字段
            dr.price * md.quantity AS subtotal,
            dr.insurance_rate
        FROM medication_detail md
        JOIN drug dr ON md.drug_id = dr.drug_id
        WHERE md.registration_id = @registration_id;

        -- 查询检查项目明细
        SELECT 
            cd.check_id,
            ci.name AS item_name,
            ci.price,
            cd.quantity,  -- 更新为使用 quantity 字段
            ci.price * cd.quantity AS subtotal,
            ci.insurance_rate
        FROM check_detail cd
        JOIN check_item ci ON cd.item_id = ci.item_id
        WHERE cd.registration_id = @registration_id;

    -- 费用信息
        SELECT 
            ISNULL(SUM(p.insurance_amount),0) AS total_insurance,
            ISNULL(SUM(p.self_pay_amount),0) AS total_self_pay,
            ISNULL(SUM(p.insurance_amount + p.self_pay_amount),0) AS total_fee
        FROM payment p
        WHERE p.registration_id = @registration_id;

    END;
    """
    with db.engine.connect() as conn:
        conn.execute(text(create_proc_sql))
        conn.commit()

    print("生成电子发票SP已经生成")
