from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import MedicalRecord, Registration, Schedule, MedicationDetail, CheckDetail, Drug, CheckItem, db,Payment
from datetime import datetime, date
from sqlalchemy.exc import SQLAlchemyError

medicalrecord = Blueprint('medicalrecord', __name__)


@medicalrecord.route('/medicalrecord', endpoint='medicalrecord_list')
@role_required('doctor')
@login_required
def list():
    if current_user.role == 'doctor' and current_user.doctor:
        # 获取当前医生的排班
        schedules = current_user.doctor.schedules.filter(
            Schedule.date == date.today()
        )
        print(f"Doctor: {current_user.doctor.name}, Schedules: {schedules.count()}")
        # 获取今天的挂号记录（包括待就诊和已就诊）
        registrations = Registration.query.filter(
            Registration.schedule_id.in_([s.schedule_id for s in schedules])
        ).all()
        print(f"Today's Registrations: {len(registrations)}")
    else:
        registrations = []
        print("No registrations found for this doctor.")

    return render_template('medicalrecord.html', registrations=registrations)


@medicalrecord.route('/medicalrecord/consult/<int:registration_id>', methods=['GET'])
@role_required('doctor')
@login_required
def consult(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    # 验证医生是否有权限为该挂号看病
    if current_user.role == 'doctor' and registration.schedule.doctor_id != current_user.doctor.doctor_id:
        flash('您无权为该患者看病')
        return redirect(url_for('medicalrecord.medicalrecord_list'))
    patient_id = registration.patient_id
    drugs = Drug.query.all()
    check_items = CheckItem.query.all()
    record = MedicalRecord.query.filter_by(registration_id=registration_id).first()
    return render_template('medicalrecord.html', record=record, patient_id=patient_id, registration_id=registration_id,
                           drugs=drugs, check_items=check_items)


@medicalrecord.route('/medicalrecord/save', methods=['POST'])
@role_required('doctor')
@login_required
def save():
    registration_id = request.form.get('registration_id')
    if not registration_id:
        flash('挂号ID不能为空')
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    try:
        # 验证挂号记录
        registration = Registration.query.get_or_404(int(registration_id))
        if current_user.role == 'doctor' and registration.schedule.doctor_id != current_user.doctor.doctor_id:
            flash('您无权为该患者保存诊疗记录')
            return redirect(url_for('medicalrecord.medicalrecord_list'))

        # 获取或创建诊疗记录
        # MedicalRecord 的主键是 registration_id，所以直接用 get 而不是 filter_by.first()
        record = MedicalRecord.query.get(int(registration_id))
        if not record:
            record = MedicalRecord(registration_id=int(registration_id))

        # 更新诊疗记录的基本信息
        record.chief_complaint = request.form.get('chief_complaint')
        record.present_illness = request.form.get('present_illness')
        record.past_history = request.form.get('past_history')
        record.allergy_history = request.form.get('allergy_history')
        record.physical_exam = request.form.get('physical_exam')
        record.diagnosis = request.form.get('diagnosis')
        record.suggestion = request.form.get('suggestion')
        record.visit_time = datetime.now()  # 更新就诊时间

        db.session.add(record) # 添加或更新 MedicalRecord

        # --- 处理用药明细和计算药品总费用 ---
        total_medication_fee = 0.0
        total_medication_insurance_amount = 0.0
        total_medication_self_pay_amount = 0.0
        new_medication_details = []

        # 删除旧的用药记录 (先删除再添加，确保更新逻辑的正确性)
        MedicationDetail.query.filter_by(registration_id=registration.registration_id).delete()

        i = 0
        while f'medication_drug_id_{i}' in request.form:
            drug_id_str = request.form.get(f'medication_drug_id_{i}')
            if drug_id_str:
                drug_id = int(drug_id_str)
                drug = Drug.query.get(drug_id) # 查询药品信息以获取价格和医保比例

                if drug:
                    # 创建新的 MedicationDetail 实例
                    # MedicationDetail 模型没有 quantity, dosage 等字段，只保存 drug_id
                    detail = MedicationDetail(
                        registration_id=registration.registration_id,
                        drug_id=drug_id
                    )
                    new_medication_details.append(detail)

                    # 费用计算：由于没有数量字段，每选择一次即算一个单位的费用
                    item_cost = drug.price
                    insurance_covered = item_cost * drug.insurance_rate
                    self_paid = item_cost - insurance_covered

                    total_medication_fee += item_cost
                    total_medication_insurance_amount += insurance_covered
                    total_medication_self_pay_amount += self_paid
            i += 1

        for detail in new_medication_details:
            db.session.add(detail) # 添加新的用药记录


        # --- 处理检查明细和计算检查总费用 ---
        total_check_fee = 0.0
        total_check_insurance_amount = 0.0
        total_check_self_pay_amount = 0.0
        new_check_details = []

        # 删除旧的检查记录
        CheckDetail.query.filter_by(registration_id=registration.registration_id).delete()

        i = 0
        while f'check_item_id_{i}' in request.form:
            item_id_str = request.form.get(f'check_item_id_{i}')
            if item_id_str:
                item_id = int(item_id_str)
                check_item = CheckItem.query.get(item_id) # 查询检查项目信息以获取价格和医保比例

                if check_item:
                    # 创建新的 CheckDetail 实例
                    # CheckDetail 的 result 字段由于前端没有输入，这里设置为 None
                    detail = CheckDetail(
                        registration_id=registration.registration_id,
                        item_id=item_id,
                        result=None
                    )
                    new_check_details.append(detail)

                    # 费用计算
                    item_cost = check_item.price
                    insurance_covered = item_cost * check_item.insurance_rate
                    self_paid = item_cost - insurance_covered

                    total_check_fee += item_cost
                    total_check_insurance_amount += insurance_covered
                    total_check_self_pay_amount += self_paid
            i += 1

        for detail in new_check_details:
            db.session.add(detail) # 添加新的检查记录


        # --- 生成 Payment 记录 ---
        # 如果有药品费用，生成一条药品支付记录
        if total_medication_fee > 0:
            payment_medication = Payment(
                registration_id=registration.registration_id,
                fee_type='药品费',
                insurance_amount=total_medication_insurance_amount,
                self_pay_amount=total_medication_self_pay_amount,
                pay_method='待支付', # 待支付状态，支付方式未知
                pay_time=datetime.now(), # 记录创建时间
                pay_status='待支付'
            )
            db.session.add(payment_medication)

        # 如果有检查费用，生成一条检查支付记录
        if total_check_fee > 0:
            payment_check = Payment(
                registration_id=registration.registration_id,
                fee_type='检查费',
                insurance_amount=total_check_insurance_amount,
                self_pay_amount=total_check_self_pay_amount,
                pay_method='待支付', # 待支付状态，支付方式未知
                pay_time=datetime.now(), # 记录创建时间
                pay_status='待支付'
            )
            db.session.add(payment_check)

        # 更新挂号状态为“已就诊”
        registration.visit_status = '已就诊'
        db.session.add(registration) # 确保 registration 对象的更新也被添加到会话

        # 提交所有更改
        db.session.commit()
        flash('诊疗记录和待支付费用已成功保存！')
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    except SQLAlchemyError as e:
        db.session.rollback() # 发生数据库错误时回滚事务
        flash(f'保存失败 (数据库错误): {str(e)}')
        # 记录详细错误到日志，方便调试
        print(f"SQLAlchemy Error during save medical record: {e}")
        return redirect(url_for('medicalrecord.consult', registration_id=registration_id))
    except Exception as e:
        db.session.rollback() # 捕获其他非数据库错误
        flash(f'保存失败: {str(e)}')
        # 记录详细错误到日志
        print(f"General Error during save medical record: {e}")
        return redirect(url_for('medicalrecord.consult', registration_id=registration_id))