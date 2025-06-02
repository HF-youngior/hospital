from app import create_app, db
from app.models import User, Patient, Doctor, Schedule, Registration, Payment, MedicalRecord, MedicationDetail, \
    CheckDetail, Drug, CheckItem
from werkzeug.security import generate_password_hash
from datetime import datetime, date

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
        drug_id=drugs[0].drug_id
    )
    check_detail = CheckDetail(
        registration_id=registrations[0].registration_id,
        item_id=check_items[0].item_id,
        result='未完成'
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