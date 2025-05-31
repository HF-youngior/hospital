# 医院信息管理系统

## 项目概述

这是一个基于 Flask 的医院信息管理系统，支持管理员、医生和患者三种角色。系统实现了用户注册登录、医生和患者管理、排班管理、挂号预约、病历管理以及支付功能。数据库支持 MSSQL 和 SQLite，当前默认使用 MSSQL。

## 主要功能

- **用户管理**：支持注册、登录和角色权限管理（管理员、医生、患者）。
- **医生管理**：管理员可以添加、编辑、删除医生信息，并为医生创建账号。
- **患者管理**：管理员可以管理患者信息，患者可查看个人信息和就诊记录。
- **排班管理**：医生排班信息管理，支持查看和编辑，管理员可添加、编辑、删除排班。
- **挂号预约**：患者可以在线预约挂号，查看挂号记录，支持取消预约。
- **病历管理**：医生可以创建和查看患者病历，包括用药和检查明细。
- **支付功能**：支持医保支付和自费支付，包含挂号费、药品费和检查费。

## 技术栈

- **后端**：Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **前端**：Jinja2 模板, Bootstrap（推测使用，因表单类中有 Bootstrap 类名）
- **数据库**：MSSQL（默认）或 SQLite
- **其他**：Werkzeug（密码加密）

## 项目结构与文件功能说明

项目采用前后端分离的设计方式：
- **HTML 文件**（位于 `templates/` 目录）：负责前端网页设计，使用 Jinja2 模板引擎动态渲染页面，支持 Bootstrap样式（基于类名推测）。
- **Python 文件**（位于 `views/` 目录及根目录）：包含后端逻辑设计，处理路由、数据库操作和业务逻辑，使用 Flask 框架。

### 文件夹和文件功能说明

#### `templates/` 目录（前端网页设计）
- **`403.html`**：403 权限错误页面，显示无权限访问提示，提供返回首页链接。
- **`available_schedules.html`**：可预约排班列表页面，展示排班信息（日期、时段、科室、医生等），患者可进行挂号预约。
- **`doctor_form.html`**：医生信息表单页面，用于新增或编辑医生信息（姓名、性别、职称等），仅限管理员操作。
- **`doctor_list.html`**：医生信息列表页面，展示所有医生信息（ID、姓名、性别等），管理员可编辑、删除或为医生创建账号。
- **`doctor_user_form.html`**：为医生创建账号的表单页面，输入用户名和密码，关联医生信息。
- **`index.html`**：总体网页排版，系统主页，根据用户角色（管理员、医生、患者）显示不同功能入口（如医生管理、挂号预约等）。
- **`login.html`**：登录页面，提供用户名和密码输入框，支持跳转注册页面。
- **`medical_record_view.html`**：诊疗记录查看页面，展示患者病历详情（主诉、诊断等）及用药、检查明细，支持一键支付费用。
- **`medicalrecord.html`**：病历管理页面，医生可查看今日挂号病人列表，创建或编辑诊疗记录，添加用药和检查明细。
- **`patient_form.html`**：患者信息表单页面，用于新增或编辑患者信息（姓名、性别、医保卡号等），仅限管理员操作。
- **`patient_list.html`**：患者信息列表页面，展示所有患者信息（ID、姓名、医保余额等），管理员可编辑或删除患者。
- **`patient_profile.html`**：患者个人中心页面，展示账号信息（用户名、角色）、患者信息（姓名、医保余额等）及就诊历史。
- **`register.html`**：注册页面，患者可输入用户名、密码和身份证号进行注册，支持自动关联患者信息。
- **`registration_list.html`**：挂号记录列表页面，展示用户挂号记录（挂号ID、患者姓名、科室等），支持取消挂号或查看病历。
- **`schedule_form.html`**：排班表单页面，用于新增或编辑排班信息（医生、日期、时段等），仅限管理员操作。
- **`schedule_list.html`**：排班信息列表页面，展示排班信息（医生、科室、日期等），管理员可编辑或删除排班。
- **`select_patient.html`**：为患者预约挂号页面，管理员选择患者并确认预约，展示排班信息。

#### `views/` 目录（后端逻辑设计）
- **`auth.py`**：认证模块，处理用户登录、注册和退出逻辑。
  - `/login`：处理登录请求，验证用户名和密码，成功后跳转主页。
  - `/register`：处理注册请求，创建患者用户，支持关联已有患者信息。
  - `/logout`：处理退出请求，清除用户登录状态。
- **`decorators.py`**：权限装饰器模块，定义 `role_required` 装饰器，用于限制路由访问权限（如仅限管理员）。
- **`doctor.py`**：医生管理模块，处理医生信息的增删改查及账号创建。
  - `/doctor/list`：展示医生列表。
  - `/doctor/add`：添加新医生。
  - `/doctor/edit/<int:doctor_id>`：编辑医生信息。
  - `/doctor/delete/<int:doctor_id>`：删除医生。
  - `/doctor/create_account/<int:doctor_id>`：为医生创建用户账号。
- **`main.py`**：主模块，处理主页路由。
  - `/`：渲染主页（`index.html`），根据用户角色显示功能入口。
- **`medicalrecord.py`**：病历管理模块，医生可查看今日挂号病人并创建/保存诊疗记录。
  - `/medicalrecord`：展示今日挂号病人列表。
  - `/medicalrecord/consult/<int:registration_id>`：创建或查看诊疗记录。
  - `/medicalrecord/save`：保存诊疗记录，包括用药和检查明细。
- **`patient.py`**：患者管理模块，处理患者信息的增删改查及个人中心功能。
  - `/patient/list`：展示患者列表。
  - `/patient/add`：添加新患者。
  - `/patient/edit/<int:patient_id>`：编辑患者信息。
  - `/patient/delete/<int:patient_id>`：删除患者。
  - `/patient/profile`：患者个人中心，展示账号信息和就诊历史。
- **`registration.py`**：挂号管理模块，处理挂号预约、取消、支付及病历查看。
  - `/registration/list`：展示挂号记录列表。
  - `/registration/available`：展示可预约排班列表。
  - `/registration/make/<int:schedule_id>`：处理挂号预约。
  - `/registration/cancel/<int:registration_id>`：取消挂号并退还费用。
  - `/registration/pay/medication/<int:record_id>`：支付药品费用。
  - `/registration/pay/check/<int:record_id>`：支付检查费用。
  - `/registration/medicalrecord/<int:registration_id>`：查看病历。
- **`schedule.py`**：排班管理模块，处理排班信息的增删改查。
  - `/schedule/list`：展示排班列表。
  - `/schedule/add`：添加新排班。
  - `/schedule/edit/<int:schedule_id>`：编辑排班信息。
  - `/schedule/delete/<int:schedule_id>`：删除排班。

#### 根目录文件（后端逻辑设计）
- **`config.py`**：配置文件，定义密钥和数据库连接（支持 MSSQL 和 SQLite）。
- **`forms.py`**：表单定义模块，包含所有 WTForms 表单类（如 `LoginForm`、`DoctorForm` 等），用于前端表单验证。
- **`init_db.py`**：数据库初始化脚本，创建表结构并插入测试数据（管理员、医生、患者等）。
- **`models.py`**：数据库模型定义，包含所有数据表结构（如 `User`、`Patient`、`Doctor` 等）。
- **`run.py`**：项目启动文件，初始化 Flask 应用并运行服务。

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <项目地址>
   cd <项目目录>
   ```

2. **创建虚拟环境并安装依赖**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows 使用 venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **配置数据库**
   - 默认使用 MSSQL，确保安装了 `ODBC Driver 17 for SQL Server`。
   - 或者在 `config.py` 中切换为 SQLite。
   - 修改 `config.py` 中的 `SECRET_KEY` 和 `SQLALCHEMY_DATABASE_URI`（如有需要）。

4. **初始化数据库**
   ```bash
   python init_db.py
   ```
   这将创建数据库表并插入初始数据，包括：
   - 管理员：用户名 `admin`，密码 `admin123`
   - 医生：用户名 `doctor1`，密码 `doctor123`
   - 患者：用户名 `patient1`，密码 `patient123`

5. **运行项目**
   ```bash
   python run.py
   ```
   访问 `http://127.0.0.1:5000` 查看系统。

## 使用说明

1. **登录**：使用初始账户登录，角色决定可见功能。
2. **管理员**：
   - 管理医生和患者信息。
   - 为医生创建账号。
   - 查看和编辑排班。
   - 访问所有功能。
3. **医生**：
   - 查看排班信息。
   - 管理患者病历。
4. **患者**：
   - 在线挂号预约。
   - 查看个人中心和就诊记录。
   - 支付药品和检查费用。
5. **支付**：挂号、药品和检查费用支持医保支付和自费支付。

## 注意事项

- 确保数据库连接正确，若使用 MSSQL，需安装相关驱动。
- 初始数据中的医保余额和号源数量仅为测试用途。
- 项目运行时，调试模式已开启（`debug=True`），生产环境请关闭。
- 权限控制依赖 `role_required` 装饰器，未登录用户或无权限用户将跳转至 403 页面。
