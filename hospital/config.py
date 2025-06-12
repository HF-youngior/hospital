import os
import urllib.parse  # 导入用于URL编码的库


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key_for_dev'  # 生产环境请使用更安全的密钥管理

    # --- SQL Server Authentication 配置 ---
    DB_SERVER_INSTANCE = 'localhost'  # 如果是默认实例，使用 'localhost' 或你的计算机名
    # 如果是命名实例，例如 SQLEXPRESS，使用 'localhost\\SQLEXPRESS' (注意双反斜杠)
    DB_NAME = 'hospitalDB'

    # 强烈建议从环境变量获取用户名和密码，而不是硬编码
    DB_USER = 'smgf'  # 替换为你的SQL Server登录名
    DB_PASSWORD_RAW = 'smgf'  # 替换为你的SQL Server密码

    ODBC_DRIVER = 'ODBC Driver 17 for SQL Server'

    # --- 对密码进行URL编码，以防密码中包含特殊字符 ---
    # 特殊字符如 @, :, /, ?, #, [, ], &, =, +, ,, $ 等在URL中需要编码
    DB_PASSWORD_ENCODED = urllib.parse.quote_plus(DB_PASSWORD_RAW)

    # --- 对驱动名中的空格进行编码 (通常用 '+' 替换即可) ---
    # 或者对整个驱动参数进行编码，如果更复杂
    ODBC_DRIVER_ENCODED_FOR_URI = ODBC_DRIVER.replace(' ', '+')
    # 如果替换空格不行，可以尝试完全编码：
    # ODBC_DRIVER_ENCODED_FOR_URI = urllib.parse.quote_plus(ODBC_DRIVER)

    # --- 构建 SQLAlchemy 数据库连接 URI ---
    # 格式: mssql+pyodbc://<username>:<password_encoded>@<server_instance>/<database_name>?driver=<driver_name_encoded>
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://"
        f"{DB_USER}:{DB_PASSWORD_ENCODED}"
        f"@{DB_SERVER_INSTANCE}/{DB_NAME}"
        f"?driver={ODBC_DRIVER_ENCODED_FOR_URI}"
    )

    # 备选：使用 odbc_connect 参数，有时对复杂连接更友好
    # odbc_connect_params_dict = {
    #     'DRIVER': f'{{{ODBC_DRIVER}}}', # ODBC connect string中的驱动名要用{}包围
    #     'SERVER': DB_SERVER_INSTANCE,
    #     'DATABASE': DB_NAME,
    #     'UID': DB_USER,
    #     'PWD': DB_PASSWORD_RAW, # 在这里用原始密码，因为整个字符串会被 quote_plus
    # }
    # odbc_connect_string = ";".join([f"{k}={v}" for k, v in odbc_connect_params_dict.items()])
    # SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(odbc_connect_string)}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False


# --- 示例：如何在你的环境中设置环境变量 (以 Windows PowerShell 为例) ---
# $env:HOSPITAL_DB_USER = "your_actual_sql_username"
# $env:HOSPITAL_DB_PASSWORD = "YourActualSQLPassword123!"
# 之后运行你的Python应用，它会从环境变量读取这些值。
# 对于 Linux/macOS (bash/zsh):
# export HOSPITAL_DB_USER="your_actual_sql_username"
# export HOSPITAL_DB_PASSWORD="YourActualSQLPassword123!"

# --- 你的 Flask 应用初始化部分 (示例) ---
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy

# app = Flask(__name__)
# app.config.from_object(Config) # 从上面的Config类加载配置
# db = SQLAlchemy(app)

# class YourTableModel(db.Model): # 替换成你实际的模型
#     __tablename__ = 'some_table_in_hospitalDB' # 假设表名
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100))

# @app.route('/')
# def home():
#     try:
#         # 尝试从数据库获取数据来测试连接
#         item_count = YourTableModel.query.count()
#         return f"Successfully connected to hospitalDB! Item count: {item_count}"
#     except Exception as e:
#         # 在开发时打印详细错误
#         import traceback
#         error_details = traceback.format_exc()
#         print(f"Database connection or query error: {e}{error_details}")
#         return f"Error connecting to database: {str(e)}"

# if __name__ == '__main__':
#     # 在应用上下文中创建表 (如果模型已定义且表不存在)
#     # with app.app_context():
#     #     db.create_all()
#     app.run(debug=True)