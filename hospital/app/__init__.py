from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# 数据库实例
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

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

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    return app