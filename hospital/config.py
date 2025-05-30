import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    
    # 修复连接字符串格式 - 使用直接格式
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://localhost/hospital?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes'
    
    # 备选方案 - SQLite
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///hospital.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False 