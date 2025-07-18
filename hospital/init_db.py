from app import create_app, db
from app.models import User, Patient, Doctor, Schedule, Registration, Payment, MedicalRecord, MedicationDetail, \
    CheckDetail, Drug, CheckItem
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
from sqlalchemy import text
import random

def random_id_card(birth):
    area_code = random.choice(['500107', '110101', '320311', '440305', '370202'])
    birth_str = birth.strftime('%Y%m%d')
    seq = f"{random.randint(100, 999)}"
    check = random.choice(list('0123456789X'))
    return f"{area_code}{birth_str}{seq}{check}"

def random_insurance_card(id_card):
    area_code = random.choice(['11', '50', '32', '44', '37'])
    id_tail = id_card[-7:-1]  # 身份证号倒数第7到倒数第2位
    rand_part = f"{random.randint(1000, 9999)}"
    return f"{area_code}{id_tail}{rand_part}"

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
        id_card = random_id_card(birth)
        insurance_card = random_insurance_card(id_card)
        pat = Patient(
            name=name,
            gender=gender,
            birth_date=birth,
            contact=f'13883373{random.randint(100,999)}',
            id_card=id_card,
            insurance_card=insurance_card,
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
    
    # 为patient1创建两条合理的诊疗记录
    patient1 = patient_users[0]  # 获取patient1的用户信息
    today = date.today()
    
    # 第一条诊疗记录 - 一周前
    sch1 = Schedule(
        doctor_id=doctor_users[0].doctor.doctor_id,
        date=today - timedelta(days=7),
        time_slot='上午',
        room_address=f"{doctor_users[0].doctor.department}诊室101",
        reg_fee=40.0,
        total_slots=10,
        remain_slots=10
    )
    db.session.add(sch1)
    db.session.flush()
    
    reg1 = Registration(
        patient_id=patient1.patient_id,
        schedule_id=sch1.schedule_id,
        reg_time=datetime.now() - timedelta(days=7),
        visit_status='已就诊'
    )
    db.session.add(reg1)
    db.session.flush()
    registrations.append(reg1)
    
    # 第二条诊疗记录 - 三天前
    sch2 = Schedule(
        doctor_id=doctor_users[1].doctor.doctor_id,
        date=today - timedelta(days=3),
        time_slot='下午',
        room_address=f"{doctor_users[1].doctor.department}诊室102",
        reg_fee=42.0,
        total_slots=10,
        remain_slots=10
    )
    db.session.add(sch2)
    db.session.flush()
    
    reg2 = Registration(
        patient_id=patient1.patient_id,
        schedule_id=sch2.schedule_id,
        reg_time=datetime.now() - timedelta(days=3),
        visit_status='已就诊'
    )
    db.session.add(reg2)
    db.session.flush()
    registrations.append(reg2)
    
    # 为其他患者创建挂号记录
    for i, pat in enumerate(patient_users[1:], 1):
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

    # 为patient1创建第一条诊疗记录的病历
    medical_record1 = MedicalRecord(
        registration_id=reg1.registration_id,
        visit_time=datetime.now() - timedelta(days=7),
        chief_complaint='头痛一周',
        present_illness='间断性头痛，无明显诱因',
        past_history='无特殊病史',
        allergy_history='无',
        physical_exam='血压正常，心肺无异常',
        diagnosis='偏头痛',
        suggestion='服用阿司匹林，观察病情'
    )
    db.session.add(medical_record1)
    db.session.flush()

    # 为patient1创建第二条诊疗记录的病历
    medical_record2 = MedicalRecord(
        registration_id=reg2.registration_id,
        visit_time=datetime.now() - timedelta(days=3),
        chief_complaint='咳嗽、发热3天',
        present_illness='3天前开始咳嗽，伴有发热，最高体温38.5℃',
        past_history='无特殊病史',
        allergy_history='无',
        physical_exam='咽部充血，双肺呼吸音粗',
        diagnosis='上呼吸道感染',
        suggestion='服用头孢克洛，多喝水，注意休息'
    )
    db.session.add(medical_record2)
    db.session.flush()

    # 为patient1第一条诊疗记录创建用药和检查明细
    medication_detail1 = MedicationDetail(
        registration_id=reg1.registration_id,
        drug_id=drugs[0].drug_id,  # 阿司匹林
        quantity=1
    )
    check_detail1 = CheckDetail(
        registration_id=reg1.registration_id,
        item_id=check_items[0].item_id,  # 血常规
        result='正常',
        quantity=1
    )
    db.session.add_all([medication_detail1, check_detail1])
    db.session.flush()

    # 为patient1第二条诊疗记录创建用药和检查明细
    medication_detail2 = MedicationDetail(
        registration_id=reg2.registration_id,
        drug_id=drugs[1].drug_id,  # 头孢克洛
        quantity=2
    )
    check_detail2 = CheckDetail(
        registration_id=reg2.registration_id,
        item_id=check_items[2].item_id,  # 心电图
        result='正常',
        quantity=1
    )
    db.session.add_all([medication_detail2, check_detail2])
    db.session.flush()

    # 为patient1创建支付记录
    patient = Patient.query.get(patient1.patient_id)
    
    # 第一条诊疗记录的支付
    drug_payment1 = Payment(
        registration_id=reg1.registration_id,
        fee_type='药品费',
        insurance_amount=drugs[0].price * 0.8,
        self_pay_amount=drugs[0].price * 0.2,
        pay_method='医保支付',
        pay_time=datetime.now() - timedelta(days=7),
        pay_status='已支付'
    )
    check_payment1 = Payment(
        registration_id=reg1.registration_id,
        fee_type='检查费',
        insurance_amount=check_items[0].price * 0.8,
        self_pay_amount=check_items[0].price * 0.2,
        pay_method='医保支付',
        pay_time=datetime.now() - timedelta(days=7),
        pay_status='已支付'
    )
    
    # 第二条诊疗记录的支付
    drug_payment2 = Payment(
        registration_id=reg2.registration_id,
        fee_type='药品费',
        insurance_amount=drugs[1].price * 0.8 * 2,  # 数量为2
        self_pay_amount=drugs[1].price * 0.2 * 2,
        pay_method='医保支付',
        pay_time=datetime.now() - timedelta(days=3),
        pay_status='已支付'
    )
    check_payment2 = Payment(
        registration_id=reg2.registration_id,
        fee_type='检查费',
        insurance_amount=check_items[2].price * 0.8,
        self_pay_amount=check_items[2].price * 0.2,
        pay_method='医保支付',
        pay_time=datetime.now() - timedelta(days=3),
        pay_status='已支付'
    )
    
    db.session.add_all([drug_payment1, check_payment1, drug_payment2, check_payment2])
    
    # 更新患者医保余额
    patient.insurance_balance -= (
        drugs[0].price * 0.8 + check_items[0].price * 0.8 +  # 第一次诊疗
        drugs[1].price * 0.8 * 2 + check_items[2].price * 0.8  # 第二次诊疗
    )

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

    # 定义科室-药品/检查项目映射
    department_drugs = {
        '儿科': ['阿莫西林', '布洛芬', '维生素C'],
        '外科': ['阿司匹林', '头孢克洛', '地塞米松'],
        '内科': ['头孢克洛', '氯雷他定', '阿莫西林'],
        '骨科': ['布洛芬', '地塞米松'],
    }
    department_checks = {
        '儿科': ['血常规', '心电图'],
        '外科': ['CT', 'B超', '胸片'],
        '内科': ['血常规', '尿常规', '心电图'],
        '骨科': ['CT', 'B超'],
    }
    for reg in registrations:
        if reg.visit_status == '已就诊':
            # 检查是否已有病历，避免重复
            if not MedicalRecord.query.filter_by(registration_id=reg.registration_id).first():
                department = reg.schedule.doctor.department if reg.schedule and reg.schedule.doctor else None
                record = MedicalRecord(
                    registration_id=reg.registration_id,
                    visit_time=datetime.now(),
                    chief_complaint=random.choice(['头痛', '咳嗽', '发热', '腹痛', '乏力']),
                    present_illness='症状持续' + str(random.randint(1, 7)) + '天',
                    past_history=random.choice(['无特殊病史', '高血压', '糖尿病', '过敏史']),
                    allergy_history=random.choice(['无', '青霉素过敏', '花粉过敏']),
                    physical_exam=random.choice(['体温正常', '咽部充血', '腹部压痛', '心肺无异常']),
                    diagnosis=random.choice(['上呼吸道感染', '胃炎', '偏头痛', '支气管炎']),
                    suggestion=random.choice(['多喝水', '注意休息', '按时服药', '复查'])
                )
                db.session.add(record)
                db.session.flush()
                # 按科室过滤药品
                drug_names = department_drugs.get(department, [d.name for d in drugs])
                dept_drugs = [d for d in drugs if d.name in drug_names]
                if dept_drugs:
                    for drug in random.sample(dept_drugs, min(2, len(dept_drugs))):
                        med_detail = MedicationDetail(
                            registration_id=reg.registration_id,
                            drug_id=drug.drug_id,
                            quantity=random.randint(1, 3)
                        )
                        db.session.add(med_detail)
                # 按科室过滤检查项目
                check_names = department_checks.get(department, [c.name for c in check_items])
                dept_checks = [c for c in check_items if c.name in check_names]
                if dept_checks:
                    for item in random.sample(dept_checks, min(2, len(dept_checks))):
                        check_detail = CheckDetail(
                            registration_id=reg.registration_id,
                            item_id=item.item_id,
                            result=random.choice(['正常', '轻度异常', '需复查']),
                            quantity=1
                        )
                        db.session.add(check_detail)
    db.session.commit()
    print("所有已就诊挂号已补全病历、用药和检查明细！")
