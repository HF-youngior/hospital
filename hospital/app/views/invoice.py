import io
import os
import re
import tempfile
from os import abort
from flask import Blueprint, send_file, abort
from fpdf import FPDF
from flask import Blueprint, request, send_file
from app.models import db, MedicalRecord
import datetime

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoice')

def sanitize_filename(name):
    """防止文件名中出现非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "_", name)

@invoice_bp.route('/generate/<int:registration_id>')
def generate(registration_id):
    medical_record = MedicalRecord.query.filter_by(registration_id=registration_id).first()
    if not medical_record:
        raise ValueError("未找到对应的病历记录")

    medical_record_id = medical_record.registration_id
    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("EXEC sp_GetMedicalRecordInfo ?", registration_id)

        # 第一结果集：病人信息
        patient_info = cursor.fetchone()
        cursor.nextset()

        # 第二结果集：药品明细
        meds = cursor.fetchall()
        cursor.nextset()

        # 第三结果集：检查项目
        checks = cursor.fetchall()
        cursor.nextset()

        # 第四结果集：费用信息
        fee = cursor.fetchone()

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(BASE_DIR, 'msyh.ttf')

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('msyh', '', font_path, uni=True)  # 加载内置中文字体
        pdf.set_font("msyh", size=12)

        # 病人信息部分
        pdf.cell(0, 10, f"患者姓名: {patient_info.patient_name}", ln=True)
        pdf.cell(0, 10, f"性别: {patient_info.gender}  出生日期: {patient_info.birth_date}", ln=True)
        pdf.cell(0, 10, f"身份证号: {patient_info.id_card}  联系方式: {patient_info.contact}", ln=True)
        pdf.cell(0, 10,
                 f"就诊时间: {patient_info.reg_time}  医生: {patient_info.doctor_name}  科室: {patient_info.department}",
                 ln=True)
        pdf.cell(0, 10, f"就诊状态: {patient_info.visit_status}", ln=True)
        pdf.ln(10)

        # 药品部分
        pdf.cell(0, 10, "药品明细：", ln=True)
        for med in meds:
            pdf.multi_cell(0, 8,
                           f"{med.drug_name} ({med.specification}) - {med.price:.2f}元  小计: {med.subtotal:.2f}元  医保比例: {med.insurance_rate * 100:.0f}%",
                           ln=True)

        pdf.ln(5)
        pdf.cell(0, 10, "检查项目：", ln=True)
        for check in checks:
            pdf.multi_cell(0, 8, f"{check.item_name} - {check.price:.2f}元  医保比例: {check.insurance_rate * 100:.0f}%",
                           ln=True)

        pdf.ln(10)
        pdf.cell(0, 10, f"总费用: {fee.total_fee:.2f}元 (医保支付: {fee.total_insurance:.2f}元, 自费: {fee.total_self_pay:.2f}元)",
                 ln=True)

        # 生成文件名：患者姓名_挂号时间.pdf
        reg_time = patient_info.reg_time.strftime('%Y%m%d%H%M') if isinstance(patient_info.reg_time,
                                                                              datetime.datetime) else str(
            patient_info.reg_time)
        filename = sanitize_filename(f"{patient_info.patient_name}_{reg_time}.pdf")

        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmpfile:
            pdf.output(tmpfile.name)
            tmpfile_path = tmpfile.name

        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        # 直接返回文件流，不写磁盘
        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    finally:
        cursor.close()
        connection.close()