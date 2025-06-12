from app import create_app, db
from app.models import User, Patient, Doctor, Schedule, Registration, Payment, MedicalRecord, MedicationDetail, \
    CheckDetail, Drug, CheckItem
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import text
import random

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

    # 1. 医生（8名，4个科室）
    doctor_infos = [
        {'name': '金珞辰', 'gender': '女', 'title': '主任医师', 'department': '外科', 'phone': '13032303383', 'status': '在职'},
        {'name': '李明辉', 'gender': '男', 'title': '副主任医师', 'department': '内科', 'phone': '13032303384', 'status': '在职'},
        {'name': '张晓红', 'gender': '女', 'title': '主治医师', 'department': '儿科', 'phone': '13032303385', 'status': '在职'},
        {'name': '王磊', 'gender': '男', 'title': '主治医师', 'department': '骨科', 'phone': '13032303386', 'status': '在职'},
        {'name': '赵敏', 'gender': '女', 'title': '主任医师', 'department': '外科', 'phone': '13032303387', 'status': '在职'},
        {'name': '孙强', 'gender': '男', 'title': '副主任医师', 'department': '内科', 'phone': '13032303388', 'status': '在职'},
        {'name': '刘洋', 'gender': '男', 'title': '主治医师', 'department': '儿科', 'phone': '13032303389', 'status': '在职'},
        {'name': '陈静', 'gender': '女', 'title': '主治医师', 'department': '骨科', 'phone': '13032303390', 'status': '在职'},
    ]
    doctor_users = []
    for i, doc in enumerate(doctor_infos, 1):
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

    # 2. 患者（15名）
    patient_names = ['杨雅涵', '王强', '刘芳', '李雷', '韩梅梅', '赵云', '钱多多', '孙悟空', '周杰伦', '吴彦祖', '郑爽', '冯雪', '陈晨', '褚明', '卫青']
    patients = []
    patient_users = []
    for i, name in enumerate(patient_names, 1):
        gender = '女' if i % 2 == 0 else '男'
        birth = date(1980 + i % 20, (i % 12) + 1, (i % 28) + 1)
        id_card = f'500107{birth.year}{birth.month:02d}{birth.day:02d}{1000+i:04d}'
        pat = Patient(
            name=name,
            gender=gender,
            birth_date=birth,
            contact=f'13883373{100+i:03d}',
            id_card=id_card,
            insurance_card=f'06137{110+i}',
            insurance_balance=random.randint(5000, 20000)
        )
        db.session.add(pat)
        db.session.flush()
        user = User(
            username=f'patient{i}',
            password_hash=generate_password_hash(f'patient{i}123', method='pbkdf2:sha256'),
            role='patient',
            id_card=pat.id_card,
            patient_id=pat.patient_id
        )
        db.session.add(user)
        db.session.flush()
        patients.append(pat)
        patient_users.append(user)

    # 3. 药品（8种）
    drugs = [
        Drug(name='阿司匹林', specification='100mg*100片', price=25.0, usage='口服', frequency='每日一次', stock=100, remark='解热镇痛', status='可用', insurance_rate=0.8),
        Drug(name='头孢克洛', specification='250mg*12粒', price=45.0, usage='口服', frequency='每日两次', stock=50, remark='抗生素', status='可用', insurance_rate=0.8),
        Drug(name='布洛芬', specification='200mg*24片', price=30.0, usage='口服', frequency='每日三次', stock=80, remark='止痛退烧', status='可用', insurance_rate=0.7),
        Drug(name='氯雷他定', specification='10mg*10片', price=18.0, usage='口服', frequency='每日一次', stock=60, remark='抗过敏', status='可用', insurance_rate=0.6),
        Drug(name='阿莫西林', specification='500mg*20粒', price=35.0, usage='口服', frequency='每日三次', stock=70, remark='抗生素', status='可用', insurance_rate=0.75),
        Drug(name='维生素C', specification='100mg*60片', price=15.0, usage='口服', frequency='每日一次', stock=90, remark='补充维生素', status='可用', insurance_rate=0.5),
        Drug(name='地塞米松', specification='0.75mg*20片', price=22.0, usage='口服', frequency='每日一次', stock=40, remark='抗炎', status='可用', insurance_rate=0.65),
        Drug(name='氨溴索', specification='30mg*10片', price=28.0, usage='口服', frequency='每日两次', stock=55, remark='化痰止咳', status='可用', insurance_rate=0.6),
    ]
    db.session.add_all(drugs)
    db.session.flush()

    # 4. 检查项目（6个）
    check_items = [
        CheckItem(name='血常规', price=50.0, department='检验科', insurance_rate=0.8),
        CheckItem(name='胸片', price=150.0, department='放射科', insurance_rate=0.8),
        CheckItem(name='心电图', price=80.0, department='心内科', insurance_rate=0.7),
        CheckItem(name='B超', price=120.0, department='超声科', insurance_rate=0.7),
        CheckItem(name='尿常规', price=40.0, department='检验科', insurance_rate=0.6),
        CheckItem(name='CT', price=300.0, department='放射科', insurance_rate=0.85),
    ]
    db.session.add_all(check_items)
    db.session.flush()

    # 5. 排班（每个医生3天2时段）
    schedules = []
    today = date.today()
    for i, doc_user in enumerate(doctor_users):
        for d in range(3):
            for slot in ['上午', '下午']:
                sch = Schedule(
                    doctor_id=doc_user.doctor.doctor_id,
                    date=today + timedelta(days=d),
                    time_slot=slot,
                    room_address=f"{doc_user.doctor.department}诊室{101+i}",
                    reg_fee=40.0 + i*2,
                    total_slots=10,
                    remain_slots=10
                )
                db.session.add(sch)
                db.session.flush()
                schedules.append(sch)

    # 6. 挂号（每个患者2-3次，状态多样）
    registrations = []
    reg_statuses = ['待就诊', '已就诊', '已取消']
    for i, pat in enumerate(patient_users):
        for j in range(random.randint(2, 3)):
            sch = random.choice(schedules)
            status = random.choices(reg_statuses, weights=[0.5, 0.4, 0.1])[0]
            reg = Registration(
                patient_id=pat.patient_id,
                schedule_id=sch.schedule_id,
                reg_time=datetime.now() - timedelta(days=random.randint(0, 5)),
                visit_status=status
            )
            db.session.add(reg)
            db.session.flush()
            registrations.append(reg)

    # 7. 诊疗记录、用药、检查明细（部分挂号有）
    for reg in registrations:
        if reg.visit_status == '已就诊':
            record = MedicalRecord(
                registration_id=reg.registration_id,
                visit_time=reg.reg_time,
                chief_complaint=random.choice(['头痛', '咳嗽', '发热', '腹痛', '乏力']),
                present_illness=random.choice(['症状反复', '偶有加重', '无明显诱因']),
                past_history=random.choice(['无特殊病史', '高血压', '糖尿病']),
                allergy_history=random.choice(['无', '青霉素过敏']),
                physical_exam=random.choice(['体温正常', '血压正常', '心肺无异常']),
                diagnosis=random.choice(['感冒', '胃炎', '支气管炎', '偏头痛']),
                suggestion=random.choice(['多喝水', '按时服药', '复查'])
            )
            db.session.add(record)
            db.session.flush()
            # 用药明细
            for _ in range(random.randint(1, 2)):
                med = MedicationDetail(
                    registration_id=reg.registration_id,
                    drug_id=random.choice(drugs).drug_id
                )
                db.session.add(med)
            # 检查明细
            for _ in range(random.randint(1, 2)):
                chk = CheckDetail(
                    registration_id=reg.registration_id,
                    item_id=random.choice(check_items).item_id,
                    result=random.choice(['正常', '异常', '未完成'])
                )
                db.session.add(chk)

    db.session.commit()
    print("数据库表已创建完成！")
    print("初始管理员账号：用户名: admin, 密码: admin123")
    print("医生账号：")
    for i in range(1, len(doctor_users)+1):
        print(f"  用户名: doctor{i}, 密码: doctor{i}123")
    print("患者账号：")
    for i, user in enumerate(patient_users, 1):
        print(f"  用户名: patient{i}, 密码: patient{i}123")

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
            1 AS quantity,
            dr.price AS subtotal,
            dr.insurance_rate
        FROM medication_detail md
        JOIN drug dr ON md.drug_id = dr.drug_id
        WHERE md.registration_id = @registration_id;

        -- 查询检查项目明细
        SELECT 
            cd.check_id,
            ci.name AS item_name,
            ci.price,
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