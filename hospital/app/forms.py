# 在此处定义WTForms表单类 
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    id_card = StringField('身份证号', validators=[DataRequired(), Length(18, 18)])
    submit = SubmitField('注册')

class DoctorForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(1, 50)])
    gender = StringField('性别', validators=[DataRequired(), Length(1, 10)])
    title = StringField('职称', validators=[DataRequired(), Length(1, 50)])
    department = StringField('所属科室', validators=[DataRequired(), Length(1, 50)])
    phone = StringField('联系电话', validators=[DataRequired(), Length(1, 20)])
    status = StringField('状态', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField('提交')

class PatientForm(FlaskForm):
    name = StringField('姓名', validators=[DataRequired(), Length(1, 50)])
    gender = StringField('性别', validators=[DataRequired(), Length(1, 10)])
    birth_date = DateField('出生日期', format='%Y-%m-%d', validators=[DataRequired()])
    contact = StringField('联系方式', validators=[DataRequired(), Length(1, 20)])
    id_card = StringField('身份证号', validators=[DataRequired(), Length(1, 20)])
    insurance_card = StringField('医保卡号', validators=[DataRequired(), Length(1, 20)])
    insurance_balance = FloatField('医保余额', validators=[DataRequired()])
    submit = SubmitField('提交')

class DoctorUserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired()])
    name = StringField('姓名', validators=[DataRequired(), Length(1, 50)])
    gender = StringField('性别', validators=[DataRequired(), Length(1, 10)])
    title = StringField('职称', validators=[DataRequired(), Length(1, 50)])
    department: StringField = StringField('所属科室', validators=[DataRequired(), Length(1, 50)])
    phone = StringField('联系电话', validators=[DataRequired(), Length(1, 20)])
    status = StringField('状态', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField('提交')


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from datetime import date


class ScheduleForm(FlaskForm):
    doctor_id = SelectField('医生', coerce=int, validators=[DataRequired()])
    date = DateField('日期', default=date.today, validators=[DataRequired()])
    time_slot = SelectField('时段', choices=[
        ('上午', '上午 (8:00-12:00)'),
        ('下午', '下午 (14:00-17:30)'),
        ('晚上', '晚上 (18:00-20:00)')
    ], validators=[DataRequired()])
    #department = StringField('科室', validators=[DataRequired(), Length(1, 50)])
    room_address = StringField('诊室地址', validators=[DataRequired(), Length(1, 100)])
    reg_fee = FloatField('挂号费', validators=[DataRequired(), NumberRange(min=0)])
    total_slots = IntegerField('号源总数', validators=[DataRequired(), NumberRange(min=1)])
    #remain_slots = IntegerField('剩余号源', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        from .models import Doctor
        # 只显示状态为"在职"的医生，按姓名排序
        self.doctor_id.choices = [
            (d.doctor_id, f"{d.name} | {d.department} | {d.title}")
            for d in Doctor.query.filter_by(status='在职').order_by(Doctor.name).all()
        ]