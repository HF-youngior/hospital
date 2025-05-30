from app import create_app, db
from app.models import User, Patient, Doctor, Schedule, Registration, Payment, PaymentDetail, MedicalRecord, MedicationDetail, CheckDetail, Drug, CheckItem
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

    # 创建医生用户
    doctor_user = User(
        username='doctor1',
        password_hash=generate_password_hash('doctor123', method='pbkdf2:sha256'),
        role='doctor'
    )
    db.session.add(doctor_user)

    # 创建患者用户
    patient_user = User(
        username='patient1',
        password_hash=generate_password_hash('patient123', method='pbkdf2:sha256'),
        role='patient',
        id_card='500107200506251646'
    )
    db.session.add(patient_user)
    db.session.flush()

    # 创建医生
    doctor = Doctor(
        name='金珞辰',
        gender='女',
        title='主任医师',
        department='外科',
        phone='13032303383',
        status='在职',
        user_id=doctor_user.id
    )
    db.session.add(doctor)

    # 创建患者
    patient = Patient(
        name='杨雅涵',
        gender='女',
        birth_date=date(2005, 6, 25),
        contact='13883373133',
        id_card='500107200506251646',
        insurance_card='061371137',
        insurance_balance=10000.0
    )
    db.session.add(patient)
    db.session.flush()

    # 关联患者用户
    patient_user.patient_id = patient.patient_id
    db.session.flush()

    # 创建排班记录
    schedule1 = Schedule(
        doctor_id=doctor.doctor_id,
        date=date(2025, 5, 29),
        time_slot='上午',
        reg_fee=50.0,
        department='外科',
        room_address='诊室101',
        total_slots=10,
        remain_slots=10
    )
    schedule2 = Schedule(
        doctor_id=doctor.doctor_id,
        date=date(2025, 5, 29),
        time_slot='下午',
        reg_fee=50.0,
        department='外科',
        room_address='诊室102',
        total_slots=10,
        remain_slots=10
    )
    db.session.add_all([schedule1, schedule2])
    db.session.flush()

    # 创建挂号记录及支付记录
    # 挂号 1：患者1，排班1，待就诊
    registration1 = Registration(
        patient_id=patient.patient_id,
        schedule_id=schedule1.schedule_id,
        reg_time=datetime(2025, 5, 29, 14, 0, 0),
        reg_type='初诊',
        visit_status='待就诊'
    )
    db.session.add(registration1)
    db.session.flush()

    # 模拟 make_registration 的支付逻辑
    reg_fee1 = schedule1.reg_fee
    insurance_rate = 0.8
    insurance_amount1 = reg_fee1 * insurance_rate
    self_pay_amount1 = reg_fee1 * (1 - insurance_rate)
    patient.insurance_balance -= insurance_amount1
    schedule1.remain_slots -= 1

    payment1 = Payment(
        patient_id=patient.patient_id,
        record_id=None,
        fee_type='挂号费',
        insurance_amount=insurance_amount1,
        self_pay_amount=self_pay_amount1,
        pay_method='医保支付',
        pay_time=datetime(2025, 5, 29, 14, 0, 0),
        pay_status='已支付'
    )
    db.session.add(payment1)
    db.session.flush()

    payment_detail1 = PaymentDetail(
        payment_id=payment1.payment_id,
        business_id=registration1.registration_id,
        fee_type='挂号费',
        amount=reg_fee1,
        detail_status='已支付'
    )
    db.session.add(payment_detail1)

    # 挂号 2：患者1，排班2，已取消
    registration2 = Registration(
        patient_id=patient.patient_id,
        schedule_id=schedule2.schedule_id,
        reg_time=datetime(2025, 5, 29, 10, 0, 0),
        reg_type='复诊',
        visit_status='已取消'
    )
    db.session.add(registration2)
    db.session.flush()

    # 支付记录（模拟已取消但保留支付记录，测试外键清理）
    reg_fee2 = schedule2.reg_fee
    insurance_amount2 = reg_fee2 * insurance_rate
    self_pay_amount2 = reg_fee2 * (1 - insurance_rate)
    # 不扣余额和余号，假设已退款和恢复

    payment2 = Payment(
        patient_id=patient.patient_id,
        record_id=None,
        fee_type='挂号费',
        insurance_amount=insurance_amount2,
        self_pay_amount=self_pay_amount2,
        pay_method='医保支付',
        pay_time=datetime(2025, 5, 29, 10, 0, 0),
        pay_status='已支付'
    )
    db.session.add(payment2)
    db.session.flush()

    payment_detail2 = PaymentDetail(
        payment_id=payment2.payment_id,
        business_id=registration2.registration_id,
        fee_type='挂号费',
        amount=reg_fee2,
        detail_status='已支付'
    )
    db.session.add(payment_detail2)

    # 创建诊疗记录
    medical_record = MedicalRecord(
        patient_id=patient.patient_id,
        registration_id=registration1.registration_id,
        chief_complaint='头痛',
        present_illness='近期头痛频繁',
        past_history='无',
        allergy_history='无',
        physical_exam='正常',
        diagnosis='偏头痛',
        suggestion='休息，多喝水'
    )
    db.session.add(medical_record)
    db.session.flush()

    # 添加药品数据
    drug1 = Drug(
        name='阿司匹林',
        specification='100mg',
        price=10.0,
        stock=100,
        remark='',
        status='可用',
        insurance_rate=0.8
    )
    drug2 = Drug(
        name='头孢克洛',
        specification='250mg',
        price=20.0,
        stock=50,
        remark='',
        status='可用',
        insurance_rate=0.7
    )
    db.session.add_all([drug1, drug2])
    db.session.flush()

    # 添加检查项目数据
    check_item1 = CheckItem(
        name='血常规',
        price=50.0,
        department='检验科',
        status='可用',
        insurance_rate=0.9
    )
    check_item2 = CheckItem(
        name='胸片',
        price=100.0,
        department='放射科',
        status='可用',
        insurance_rate=0.8
    )
    db.session.add_all([check_item1, check_item2])
    db.session.flush()

    # 添加药品明细及支付记录
    medication_detail = MedicationDetail(
        record_id=medical_record.id,
        drug_id=drug1.drug_id,
        plan_id=None
    )
    db.session.add(medication_detail)
    db.session.flush()

    # 模拟 pay_medication 的支付逻辑
    drug_price = drug1.price
    drug_insurance_rate = drug1.insurance_rate
    drug_insurance_amount = drug_price * drug_insurance_rate
    drug_self_pay_amount = drug_price * (1 - drug_insurance_rate)
    patient.insurance_balance -= drug_insurance_amount

    drug_payment = Payment(
        patient_id=patient.patient_id,
        record_id=medical_record.id,
        fee_type='药品费',
        insurance_amount=drug_insurance_amount,
        self_pay_amount=drug_self_pay_amount,
        pay_method='医保支付',
        pay_time=datetime.now(),
        pay_status='已支付'
    )
    db.session.add(drug_payment)
    db.session.flush()

    drug_payment_detail = PaymentDetail(
        payment_id=drug_payment.payment_id,
        business_id=medication_detail.detail_id,
        fee_type='药品费',
        amount=drug_price,
        detail_status='已支付'
    )
    db.session.add(drug_payment_detail)

    # 添加检查明细及支付记录
    check_detail = CheckDetail(
        record_id=medical_record.id,
        item_id=check_item1.item_id,
        status='未检查'
    )
    db.session.add(check_detail)
    db.session.flush()

    # 模拟检查的支付逻辑
    check_price = check_item1.price
    check_insurance_rate = check_item1.insurance_rate
    check_insurance_amount = check_price * check_insurance_rate
    check_self_pay_amount = check_price * (1 - check_insurance_rate)
    patient.insurance_balance -= check_insurance_amount

    check_payment = Payment(
        patient_id=patient.patient_id,
        record_id=medical_record.id,
        fee_type='检查费',
        insurance_amount=check_insurance_amount,
        self_pay_amount=check_self_pay_amount,
        pay_method='保险支付',
        pay_time=datetime.now(),
        pay_status='已支付'
    )
    db.session.add(check_payment)
    db.session.flush()

    check_payment_detail = PaymentDetail(
        payment_id=check_payment.payment_id,
        business_id=check_detail.detail_id,
        fee_type='检查费',
        amount=check_price,
        detail_status='已支付'
    )
    db.session.add(check_payment_detail)

    db.session.commit()

    print("数据库表已创建完成！")
    print("初始管理员账号已创建 - 用户名: admin, 密码: admin123")
    print("医生账号已创建 - 用户名: doctor1, 密码: doctor123")
    print("患者账户已创建 - 用户名: patient1, 密码: patient123")