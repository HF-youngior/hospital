from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, db, Patient
from app.forms import LoginForm, RegisterForm

# 用户注册时，系统会尝试根据用户提供的身份证号 (form.id_card.data) 去 Patient 表中查找是否已存在该患者的记录。
# 如果找到，新创建的 User 记录会通过 user.patient_id = patient.patient_id 与该 Patient 记录关联起来。这假设 User 模型有一个 patient_id 字段作为外键指向 Patient 表的主键。
# 如果未找到，用户仍然可以注册成功，但会收到提示，告知其患者信息未关联，需要联系医院处理。
# 这个 auth.py 文件是 Web 应用中非常标准和关键的一部分，它实现了用户管理的基础功能。

auth = Blueprint('auth', __name__)

# 路由 URL 为 /login，支持 GET 和 POST 请求
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()# 实例化登录表单 (LoginForm 定义在 app/forms.py)

    if form.validate_on_submit():
        # 如果表单验证通过，尝试从数据库中查找用户
        # form.username.data 获取表单中 'username' 字段的值
        user = User.query.filter_by(username=form.username.data).first()

        # user.password_hash 是数据库中存储的哈希密码
        # form.password.data 是用户在表单中输入的密码
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)# 调用 flask_login 的 login_user 函数，标记用户为已登录
            # 重定向到主页 (main 蓝图下的 index 视图)
            return redirect(url_for('main.index'))
        flash('用户名或密码错误')
    return render_template('login.html', form=form)

# 4. 定义注册路由和视图函数
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # 检查用户名是否存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已存在')
        else:
            # 检查是否有匹配的患者记录
            patient = Patient.query.filter_by(id_card=form.id_card.data).first()
            
            # 创建用户，使用pbkdf2:sha256算法
            user = User(
                username=form.username.data,
                password_hash=generate_password_hash(form.password.data, method='pbkdf2:sha256'),
                role='patient',
                id_card=form.id_card.data
            )
            
            # 如果找到匹配的患者记录，进行关联
            if patient:
                user.patient_id = patient.patient_id
                message = '注册成功，您的账号已与患者信息关联！'
            else:
                message = '注册成功，但未找到匹配的患者信息。请联系医院前台完善信息。'
                
            db.session.add(user)# 将新用户对象添加到数据库会话中
            db.session.commit() # 提交会话，将更改保存到数据库
            flash(message)
            return redirect(url_for('auth.login'))
            
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 