# 医院信息管理系统

## 项目简介
基于 Flask + SQL Server 的医院信息管理系统，包含用户登录、权限管理及多种业务模块。

## 主要依赖
- Flask
- Flask-Login
- Flask-WTF
- Flask-SQLAlchemy
- pyodbc

## 项目结构
```
hospital/
│
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── views/
│   ├── templates/
│   ├── static/
│   └── forms.py
├── config.py
├── run.py
├── requirements.txt
└── README.md
```

## 启动方式
1. 安装依赖：`pip install -r requirements.txt`
2. 配置数据库连接（修改 config.py）
3. 启动项目：`python run.py` 