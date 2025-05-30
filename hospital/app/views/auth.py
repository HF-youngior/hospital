from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, db, Patient
from app.forms import LoginForm, RegisterForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('用户名或密码错误')
    return render_template('login.html', form=form)

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
                
            db.session.add(user)
            db.session.commit()
            flash(message)
            return redirect(url_for('auth.login'))
            
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 