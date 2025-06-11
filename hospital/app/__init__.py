from flask import Flask, render_template # Flask 核心功能, 模板渲染函数
from flask_sqlalchemy import SQLAlchemy # ORM (对象关系映射器)，用于数据库交互
from flask_login import LoginManager # 用于用户会话管理 (登录/注销)
from config import Config

# 数据库实例
db = SQLAlchemy()  # 创建一个 SQLAlchemy 数据库实例。
login_manager = LoginManager() # 创建一个 LoginManager 实例。
# 告诉 Flask-Login 哪个视图函数处理登录。
# 如果一个用户尝试访问一个需要登录 (@login_required 装饰的) 页面但未登录，
# 他们将被重定向到 'auth.login' 路由。
# 'auth' 是蓝图的名称，'login' 是该蓝图中的视图函数名。
login_manager.login_view = 'auth.login'

# 定义应用工厂函数
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)

    # 蓝图注册（放在此处）
    with app.app_context():
        from app.views.auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)
        from app.views.main import main as main_blueprint
        app.register_blueprint(main_blueprint)
        from app.views.patient import patient_bp
        app.register_blueprint(patient_bp)
        from app.views.doctor import doctor_bp
        app.register_blueprint(doctor_bp)
        from app.views.schedule import schedule_bp
        app.register_blueprint(schedule_bp)
        from app.views.registration import registration_bp
        app.register_blueprint(registration_bp)
        from app.views.medicalrecord import medicalrecord  # 修正：改为 medicalrecord
        app.register_blueprint(medicalrecord)  # 修正：使用 medicalrecord
        from app.views.invoice import invoice_bp
        app.register_blueprint(invoice_bp)
        from app.views.inventory import inventory
        app.register_blueprint(inventory)

        # 之前创造了login_manager实例，
    # user_loader这是 login_manager 对象的一个方法，这个方法本身被设计成一个装饰器。
    # 当你把它用作装饰器时（即在函数定义前加上 @ 符号），它会把你紧随其后定义的函数（在这里是 load_user 函数）注册给 login_manager。
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app