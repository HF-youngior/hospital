from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.views.decorators import role_required
from app.models import MedicalRecord, Registration, Schedule, MedicationDetail, CheckDetail, Drug, CheckItem, db, Payment
from datetime import datetime, date
from sqlalchemy.exc import SQLAlchemyError
from app.views.inventory import SearchForm
import logging
from sqlalchemy import and_

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

medicalrecord = Blueprint('medicalrecord', __name__)

@medicalrecord.route('/medicalrecord', endpoint='medicalrecord_list')
@login_required
def list():
    search_patient = request.args.get('search_patient', '').strip()
    search_date = request.args.get('search_date', '').strip()
    if current_user.role == 'doctor' and current_user.doctor:
        schedules = current_user.doctor.schedules.filter(
            Schedule.date == date.today()
        )
        registrations = Registration.query.filter(
            Registration.schedule_id.in_([s.schedule_id for s in schedules]),
            Registration.visit_status != '已取消'
        )
    elif current_user.role == 'admin':
        # 管理员可查看所有挂号记录
        registrations = Registration.query.filter(Registration.visit_status != '已取消')
    else:
        registrations = Registration.query.filter(False)  # 空结果

    # 支持按患者姓名/ID和日期联合查询
    if search_patient:
        if search_patient.isdigit():
            registrations = registrations.filter(Registration.patient_id == int(search_patient))
        else:
            from app.models import Patient
            registrations = registrations.join(Patient).filter(Patient.name.contains(search_patient))
    if search_date:
        registrations = registrations.join(Schedule).filter(Schedule.date == search_date)
    registrations = registrations.all()
    return render_template('medicalrecord.html', registrations=registrations, search_patient=search_patient, search_date=search_date)

@medicalrecord.route('/medicalrecord/consult/<int:registration_id>', methods=['GET', 'POST'])
@role_required('doctor')
@login_required
def consult(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    # 验证医生是否有权限为该挂号看病
    if current_user.role == 'doctor' and registration.schedule.doctor_id != current_user.doctor.doctor_id:
        flash('您无权为该患者看病', 'danger')
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    patient_id = registration.patient_id
    record = MedicalRecord.query.filter_by(registration_id=registration_id).first()

    # 药品搜索
    drug_form = SearchForm()
    drugs = Drug.query.all()

    # 检查项目搜索
    check_form = SearchForm()
    check_items = CheckItem.query.all()

    # 表单数据
    form_data = {
        'chief_complaint': request.form.get('chief_complaint', record.chief_complaint if record else ''),
        'present_illness': request.form.get('present_illness', record.present_illness if record else ''),
        'past_history': request.form.get('past_history', record.past_history if record else ''),
        'allergy_history': request.form.get('allergy_history', record.allergy_history if record else ''),
        'physical_exam': request.form.get('physical_exam', record.physical_exam if record else ''),
        'diagnosis': request.form.get('diagnosis', record.diagnosis if record else ''),
        'suggestion': request.form.get('suggestion', record.suggestion if record else '')
    }

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        logger.debug(f"Received POST request with form_type: {form_type}")
        logger.debug(f"Form data: {request.form}")

        # 药品搜索
        if form_type == 'drug_search' and drug_form.validate_on_submit():
            query = drug_form.query.data
            if drug_form.search_type.data == 'name':
                drugs = Drug.query.filter(Drug.name.ilike(f'%{query}%')).all()
                logger.debug(f"Drug search query: {query}, found: {[drug.name for drug in drugs]}")
            else:  # search by ID
                try:
                    drugs = Drug.query.filter_by(drug_id=int(query)).all()
                except ValueError:
                    flash('请输入有效的药品ID', 'danger')
                    drugs = []
            if not drugs:
                flash('未找到匹配的药品', 'warning')

        # 检查项目搜索
        elif form_type == 'check_search' and check_form.validate_on_submit():
            query = check_form.query.data
            if check_form.search_type.data == 'name':
                check_items = CheckItem.query.filter(CheckItem.name.ilike(f'%{query}%')).all()
                logger.debug(f"Check search query: {query}, found: {[item.name for item in check_items]}")
            else:  # search by ID
                try:
                    check_items = CheckItem.query.filter_by(item_id=int(query)).all()
                except ValueError:
                    flash('请输入有效的检查项目ID', 'danger')
                    check_items = []
            if not check_items:
                flash('未找到匹配的检查项目', 'warning')

        else:
            flash('表单验证失败或未知表单类型', 'danger')
            logger.debug(f"Form errors: drug_form={drug_form.errors}, check_form={check_form.errors}")

    # 已选药品和检查项目
    selected_medications = MedicationDetail.query.filter_by(registration_id=registration_id).all()
    selected_checks = CheckDetail.query.filter_by(registration_id=registration_id).all()

    return render_template(
        'medicalrecord.html',
        record=record,
        patient_id=patient_id,
        registration_id=registration_id,
        drug_form=drug_form,
        check_form=check_form,
        drugs=drugs,
        check_items=check_items,
        selected_medications=selected_medications,
        selected_checks=selected_checks,
        form_data=form_data
    )

@medicalrecord.route('/medicalrecord/save', methods=['POST'])
@role_required('doctor')
@login_required
def save():
    logger.debug("Entering save route")
    registration_id = request.form.get('registration_id')
    if not registration_id:
        flash('挂号ID不能为空', 'danger')
        logger.debug("Missing registration_id")
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    try:
        # 验证挂号记录
        registration = Registration.query.get_or_404(int(registration_id))
        if current_user.role == 'doctor' and registration.schedule.doctor_id != current_user.doctor.doctor_id:
            flash('您无权为该患者保存诊疗记录', 'danger')
            logger.debug("Unauthorized doctor access")
            return redirect(url_for('medicalrecord.medicalrecord_list'))

        # 获取或创建诊疗记录
        record = MedicalRecord.query.get(int(registration_id))
        if not record:
            record = MedicalRecord(registration_id=int(registration_id))

        # 更新诊疗记录
        record.chief_complaint = request.form.get('chief_complaint')
        record.present_illness = request.form.get('present_illness')
        record.past_history = request.form.get('past_history')
        record.allergy_history = request.form.get('allergy_history')
        record.physical_exam = request.form.get('physical_exam')
        record.diagnosis = request.form.get('diagnosis')
        record.suggestion = request.form.get('suggestion')
        record.visit_time = datetime.now()
        db.session.add(record)

        # 处理用药明细
        total_medication_fee = 0.0
        total_medication_insurance_amount = 0.0
        total_medication_self_pay_amount = 0.0
        MedicationDetail.query.filter_by(registration_id=registration.registration_id).delete()

        medication_data = request.form.getlist('medications[]')
        logger.debug(f"Medication data: {medication_data}")
        new_medication_details = []
        for med in medication_data:
            if med == 'none':
                continue
            drug_id, quantity = map(int, med.split(':'))
            drug = Drug.query.get(drug_id)
            if not drug:
                flash(f'药品ID {drug_id} 不存在', 'danger')
                logger.debug(f"Drug ID {drug_id} not found")
                continue
            if drug.stock < quantity:
                flash(f'药品 {drug.name} 库存不足（剩余 {drug.stock}）', 'danger')
                logger.debug(f"Insufficient stock for {drug.name}: {drug.stock} < {quantity}")
                continue
            if quantity <= 0:
                flash(f'药品 {drug.name} 数量必须大于 0', 'danger')
                logger.debug(f"Invalid quantity for {drug.name}: {quantity}")
                continue

            detail = MedicationDetail(
                registration_id=registration.registration_id,
                drug_id=drug_id,
                quantity=quantity
            )
            new_medication_details.append(detail)

            # 更新库存
            drug.stock -= quantity
            db.session.add(drug)

            # 费用计算
            item_cost = drug.price * quantity
            insurance_covered = item_cost * drug.insurance_rate
            self_paid = item_cost - insurance_covered
            total_medication_fee += item_cost
            total_medication_insurance_amount += insurance_covered
            total_medication_self_pay_amount += self_paid

        for detail in new_medication_details:
            db.session.add(detail)

        # 处理检查明细
        total_check_fee = 0.0
        total_check_insurance_amount = 0.0
        total_check_self_pay_amount = 0.0
        CheckDetail.query.filter_by(registration_id=registration.registration_id).delete()

        check_data = request.form.getlist('checks[]')
        check_results = request.form.getlist('check_results[]')  # 获取检查结果
        logger.debug(f"Check data: {check_data}")
        logger.debug(f"Check results: {check_results}")
        
        new_check_details = []
        for i, chk in enumerate(check_data):
            if chk == 'none':
                continue
            item_id = int(chk.split(':')[0])
            check_item = CheckItem.query.get(item_id)
            if not check_item:
                flash(f'检查项目ID {item_id} 不存在', 'danger')
                logger.debug(f"Check item ID {item_id} not found")
                continue

            # 获取对应的检查结果，如果没有对应的结果则默认为"无"
            check_result = check_results[i] if i < len(check_results) else "无"

            detail = CheckDetail(
                registration_id=registration.registration_id,
                item_id=item_id,
                quantity=1,  # 检查项目固定数量为 1
                result=check_result
            )
            new_check_details.append(detail)

            # 只有当检查结果不是"无"时才计算费用
            if check_result.lower() != "无":
                # 费用计算
                item_cost = check_item.price
                insurance_covered = item_cost * check_item.insurance_rate
                self_paid = item_cost - insurance_covered
                total_check_fee += item_cost
                total_check_insurance_amount += insurance_covered
                total_check_self_pay_amount += self_paid

        for detail in new_check_details:
            db.session.add(detail)

        # 生成支付记录
        if total_medication_fee > 0:
            payment_medication = Payment(
                registration_id=registration.registration_id,
                fee_type='药品费',
                insurance_amount=total_medication_insurance_amount,
                self_pay_amount=total_medication_self_pay_amount,
                pay_method='待支付',
                pay_time=datetime.now(),
                pay_status='待支付'
            )
            db.session.add(payment_medication)

        # 只有当有实际检查费用时才创建检查费支付记录
        if total_check_fee > 0:
            payment_check = Payment(
                registration_id=registration.registration_id,
                fee_type='检查费',
                insurance_amount=total_check_insurance_amount,
                self_pay_amount=total_check_self_pay_amount,
                pay_method='待支付',
                pay_time=datetime.now(),
                pay_status='待支付'
            )
            db.session.add(payment_check)

        # 更新挂号状态
        registration.visit_status = '已就诊'
        db.session.add(registration)

        db.session.commit()
        flash('医疗记录和费用已成功保存！', 'success')
        logger.debug("Record saved successfully")
        return redirect(url_for('medicalrecord.medicalrecord_list'))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'保存失败 (数据库错误): {str(e)}', 'danger')
        logger.error(f"Database error: {str(e)}")
        return redirect(url_for('medicalrecord.consult', registration_id=registration_id))
    except Exception as e:
        db.session.rollback()
        flash(f'保存失败: {str(e)}', 'danger')
        logger.error(f"General error: {str(e)}")
        return redirect(url_for('medicalrecord.consult', registration_id=registration_id))

@medicalrecord.route('/medicalrecord/search_drugs')
@role_required('doctor')
@login_required
def search_drugs():
    search_type = request.args.get('type', 'name')
    query = request.args.get('query', '')
    registration_id = request.args.get('registration_id')
    
    if not query:
        return jsonify({'drugs': []})
    
    try:
        if search_type == 'name':
            drugs = Drug.query.filter(Drug.name.ilike(f'%{query}%')).all()
        else:  # search by ID
            try:
                drugs = Drug.query.filter_by(drug_id=int(query)).all()
            except ValueError:
                return jsonify({'error': '请输入有效的药品ID'}), 400
        
        return jsonify({
            'drugs': [{
                'drug_id': drug.drug_id,
                'name': drug.name,
                'specification': drug.specification,
                'stock': drug.stock,
                'price': float(drug.price),
                'insurance_rate': float(drug.insurance_rate)
            } for drug in drugs]
        })
    except Exception as e:
        logger.error(f"Error searching drugs: {str(e)}")
        return jsonify({'error': '搜索药品时发生错误'}), 500

@medicalrecord.route('/medicalrecord/search_checks')
@role_required('doctor')
@login_required
def search_checks():
    search_type = request.args.get('type', 'name')
    query = request.args.get('query', '')
    registration_id = request.args.get('registration_id')
    
    if not query:
        return jsonify({'checks': []})
    
    try:
        if search_type == 'name':
            checks = CheckItem.query.filter(CheckItem.name.ilike(f'%{query}%')).all()
        else:  # search by ID
            try:
                checks = CheckItem.query.filter_by(item_id=int(query)).all()
            except ValueError:
                return jsonify({'error': '请输入有效的检查项目ID'}), 400
        
        return jsonify({
            'checks': [{
                'item_id': check.item_id,
                'name': check.name,
                'department': check.department,
                'price': float(check.price),
                'insurance_rate': float(check.insurance_rate)
            } for check in checks]
        })
    except Exception as e:
        logger.error(f"Error searching checks: {str(e)}")
        return jsonify({'error': '搜索检查项目时发生错误'}), 500