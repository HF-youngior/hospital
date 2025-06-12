import io
import os
import re
import tempfile
from os import abort
from flask import Blueprint, send_file, abort
from fpdf import FPDF
from flask import Blueprint, request, send_file
from app.models import db, MedicalRecord, Registration, Payment, MedicationDetail, CheckDetail
import datetime
from flask_login import login_required, current_user
import random

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoice')

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def generate_invoice_code():
    """生成发票代码
    格式：144（地区代码）+ 001（行业代码）+ 900（医院代码）+ 111（批次号）
    例如：144001900111
    """
    return "144001900111"  # 固定代码

def generate_invoice_number():
    """生成发票号码
    格式：8位数字，按日期从00000001开始递增
    例如：202403150001
    """
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    # 这里应该从数据库获取当天的最大发票号码，然后加1
    # 为了演示，我们使用随机数
    random_num = random.randint(1, 9999)
    return f"{random_num:08d}"

@invoice_bp.route('/generate/<int:registration_id>')
@login_required
def generate(registration_id):
    # 获取挂号信息
    registration = Registration.query.get_or_404(registration_id)
    
    # 权限检查
    if current_user.role == 'patient' and current_user.patient_id != registration.patient_id:
        abort(403)
    
    # 获取患者信息
    patient_info = registration.patient
    
    # 获取支付信息
    payments = Payment.query.filter_by(registration_id=registration_id).all()
    
    # 生成发票代码和号码
    invoice_code = generate_invoice_code()
    invoice_number = generate_invoice_number()
    
    # 创建PDF
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # 添加中文字体支持
    font_path = os.path.join(os.environ['WINDIR'], 'Fonts', 'simsun.ttc')
    if not os.path.exists(font_path):
        font_path = os.path.join(os.environ['WINDIR'], 'Fonts', 'simhei.ttf')
    pdf.add_font('SimSun', '', font_path, uni=True)
    pdf.set_font('SimSun', '', 10)
    
    # 设置页面边距和自动分页
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, margin=15)
    
    # 获取页面宽度
    page_width = pdf.w - 2 * pdf.l_margin
    
    # 医院信息头部
    pdf.set_font('SimSun', '', 14)
    pdf.cell(0, 10, '医院门诊发票', ln=True, align='C')
    pdf.set_font('SimSun', '', 10)
    pdf.cell(0, 8, '发票代码：' + invoice_code, ln=True)
    pdf.cell(0, 8, '发票号码：' + invoice_number, ln=True)
    pdf.cell(0, 8, '开票日期：' + datetime.datetime.now().strftime('%Y-%m-%d'), ln=True)
    pdf.ln(5)
    
    # 患者信息
    pdf.set_font('SimSun', '', 10)
    pdf.cell(40, 8, '姓名：' + patient_info.name, ln=0)
    pdf.cell(40, 8, '性别：' + patient_info.gender, ln=0)
    pdf.cell(40, 8, '年龄：' + str((datetime.datetime.now().date() - patient_info.birth_date).days // 365), ln=True)
    pdf.cell(40, 8, '医保卡号：' + patient_info.insurance_card, ln=0)
    pdf.cell(40, 8, '身份证号：' + patient_info.id_card, ln=True)
    pdf.ln(5)
    
    # 就诊信息
    pdf.cell(40, 8, '就诊科室：' + registration.schedule.doctor.department, ln=0)
    pdf.cell(40, 8, '医生姓名：' + registration.schedule.doctor.name, ln=True)
    pdf.cell(40, 8, '就诊日期：' + registration.schedule.date.strftime('%Y-%m-%d'), ln=0)
    pdf.cell(40, 8, '就诊时段：' + registration.schedule.time_slot, ln=True)
    pdf.ln(5)
    
    # 费用明细表头
    pdf.set_fill_color(240, 240, 240)
    col_widths = [60, 30, 20, 30, 40]
    headers = ['项目', '单价', '数量', '金额', '医保比例']
    for width, header in zip(col_widths, headers):
        pdf.cell(width, 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    # 挂号费
    pdf.cell(col_widths[0], 8, '挂号费', 1, 0)
    pdf.cell(col_widths[1], 8, f"{registration.schedule.reg_fee:.2f}", 1, 0, 'R')
    pdf.cell(col_widths[2], 8, '1', 1, 0, 'C')
    pdf.cell(col_widths[3], 8, f"{registration.schedule.reg_fee:.2f}", 1, 0, 'R')
    pdf.cell(col_widths[4], 8, '80%', 1, 1, 'C')
    
    # 药品费用
    meds = MedicationDetail.query.filter_by(registration_id=registration_id).all()
    for med in meds:
        pdf.cell(col_widths[0], 8, f"{med.drug.name} ({med.drug.specification})", 1, 0)
        pdf.cell(col_widths[1], 8, f"{med.drug.price:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[2], 8, str(med.quantity), 1, 0, 'C')
        pdf.cell(col_widths[3], 8, f"{med.drug.price * med.quantity:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[4], 8, f"{med.drug.insurance_rate * 100:.0f}%", 1, 1, 'C')
    
    # 检查费用
    checks = CheckDetail.query.filter_by(registration_id=registration_id).all()
    for check in checks:
        pdf.cell(col_widths[0], 8, check.check_item.name, 1, 0)
        pdf.cell(col_widths[1], 8, f"{check.check_item.price:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[2], 8, '1', 1, 0, 'C')
        pdf.cell(col_widths[3], 8, f"{check.check_item.price:.2f}", 1, 0, 'R')
        pdf.cell(col_widths[4], 8, f"{check.check_item.insurance_rate * 100:.0f}%", 1, 1, 'C')
    
    # 费用汇总
    total_fee = sum(p.insurance_amount + p.self_pay_amount for p in payments)
    total_insurance = sum(p.insurance_amount for p in payments)
    total_self_pay = sum(p.self_pay_amount for p in payments)
    
    pdf.ln(5)
    pdf.set_font('SimSun', '', 10)
    pdf.cell(0, 8, f"总金额：{total_fee:.2f}", ln=True)
    pdf.cell(0, 8, f"医保支付：{total_insurance:.2f}", ln=True)
    pdf.cell(0, 8, f"自费金额：{total_self_pay:.2f}", ln=True)
    
    # 底部信息
    pdf.ln(10)
    pdf.set_font('SimSun', '', 9)
    pdf.cell(0, 8, '注意事项：', ln=True)
    
    # 使用cell而不是multi_cell来显示注意事项
    notes = [
        '1. 本发票为电子发票，与纸质发票具有同等法律效力。',
        '2. 请妥善保管，遗失不补。',
        '3. 如有疑问，请联系医院收费处。'
    ]
    for note in notes:
        pdf.cell(0, 6, note, ln=True)
    
    # 生成文件名
    reg_time = registration.reg_time.strftime('%Y%m%d%H%M') if isinstance(registration.reg_time, datetime.datetime) else str(registration.reg_time)
    filename = sanitize_filename(f"{patient_info.name}_{reg_time}.pdf")
    
    # 输出PDF
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    
    return send_file(
        pdf_output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )