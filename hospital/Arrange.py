from datetime import date, timedelta
# 确保这里的导入路径正确，根据你的项目结构调整
# 例如，如果 init_schedule_script.py 在项目根目录，app 是一个子目录:
from app import create_app, db
from app.models import Doctor, Schedule  # 假设模型在 app.models 中

# --- 配置参数 ---
START_DATE = date(2025, 7, 1)  # 排班开始日期，例如下个月的第一天
END_DATE = date(2025, 7, 31)  # 排班结束日期，例如下个月的最后一天

# 定义医生的排班模板
# 结构: { "科室名称": { "医生姓名": {"days_of_week": [0-6], "time_slot": "上午/下午/晚上", "room_address": "xxx", "reg_fee": xx.x, "total_slots": xx}, ... }, ... }
# days_of_week: 0=周一, 1=周二, ..., 6=周日
DOCTOR_SCHEDULE_TEMPLATES = {
    "内科": {
        "王医生": {"days_of_week": [0, 2, 4], "time_slot": "上午", "room_address": "内科诊室 A101", "reg_fee": 25.0,
                   "total_slots": 20},
        "李医生": {"days_of_week": [1, 3], "time_slot": "下午", "room_address": "内科诊室 A102", "reg_fee": 20.0,
                   "total_slots": 15},
    },
    "外科": {
        "张医生": {"days_of_week": [0, 1, 2, 3, 4], "time_slot": "上午", "room_address": "外科诊室 B201",
                   "reg_fee": 30.0, "total_slots": 25},
        "赵医生": {"days_of_week": [1, 3, 5], "time_slot": "晚上", "room_address": "外科急诊 B202", "reg_fee": 50.0,
                   "total_slots": 10},
    },
    "儿科": {
        "孙医生": {"days_of_week": [0, 2, 4], "time_slot": "下午", "room_address": "儿科诊室 C301", "reg_fee": 22.0,
                   "total_slots": 18},
    }
    # 你可以根据需要添加更多科室和医生，或者修改这里的示例
}

# 为不在模板中的医生设置的通用规则 (可选)
GENERAL_SETTINGS_ENABLED = True  # 是否为不在模板中的医生启用通用排班
GENERAL_WORK_DAYS = [0, 1, 2, 3, 4]  # 例如，默认周一到周五
GENERAL_TIME_SLOT = "上午"
GENERAL_ROOM_ADDRESS = "综合诊室 Z001"
GENERAL_REG_FEE = 15.0
GENERAL_TOTAL_SLOTS = 10


def generate_schedules_for_period(app_instance):
    with app_instance.app_context():
        all_active_doctors = Doctor.query.filter_by(status='在职').all()
        if not all_active_doctors:
            print("数据库中没有状态为“在职”的医生，无法进行排班。")
            return

        doctors_in_template = set()  # 用于记录哪些医生已通过模板处理
        schedules_to_add = []
        schedules_skipped_count = 0
        schedules_created_count = 0

        print("--- 开始处理模板定义的医生排班 ---")
        for department_name, doctors_in_dept_template in DOCTOR_SCHEDULE_TEMPLATES.items():
            for doctor_name, rules in doctors_in_dept_template.items():
                # 尝试通过科室和姓名找到医生实体
                # 假设 Doctor 模型中有 name 和 department 字段
                doctor = Doctor.query.filter_by(name=doctor_name, department=department_name, status='在职').first()

                if not doctor:
                    print(
                        f"警告：模板中的医生 '{doctor_name}' (科室: {department_name}) 未在数据库中找到或非在职，已跳过。")
                    continue

                doctors_in_template.add(doctor.doctor_id)

                current_date = START_DATE
                while current_date <= END_DATE:
                    if current_date.weekday() in rules["days_of_week"]:
                        # 检查是否已存在该排班 (使用 Doctor ID, date, time_slot)
                        if not Schedule.slot_exists(doctor.doctor_id, current_date, rules["time_slot"]):
                            new_schedule = Schedule(
                                doctor_id=doctor.doctor_id,
                                date=current_date,
                                time_slot=rules["time_slot"],
                                department=doctor.department,  # 从医生对象获取科室信息
                                room_address=rules["room_address"],
                                reg_fee=rules["reg_fee"],
                                total_slots=rules["total_slots"],
                                remain_slots=rules["total_slots"]  # 初始剩余号源等于总号源
                            )
                            schedules_to_add.append(new_schedule)
                            schedules_created_count += 1
                            # print(f"准备为 {doctor.name} ({doctor.department}) 在 {current_date} {rules['time_slot']} 创建排班。")
                        else:
                            schedules_skipped_count += 1
                            # print(f"跳过：{doctor.name} ({doctor.department}) 在 {current_date} {rules['time_slot']} 已有排班。")
                    current_date += timedelta(days=1)

        print(f"--- 模板处理完毕。准备创建 {schedules_created_count} 条，跳过 {schedules_skipped_count} 条 ---")

        if GENERAL_SETTINGS_ENABLED:
            print("--- 开始处理通用规则的医生排班 ---")
            general_schedules_created_count = 0
            general_schedules_skipped_count = 0
            for doctor in all_active_doctors:
                if doctor.doctor_id not in doctors_in_template:  # 只处理不在模板中的医生
                    # print(f"为医生 {doctor.name} ({doctor.department}) 应用通用排班规则...")
                    current_date = START_DATE
                    while current_date <= END_DATE:
                        if current_date.weekday() in GENERAL_WORK_DAYS:
                            if not Schedule.slot_exists(doctor.doctor_id, current_date, GENERAL_TIME_SLOT):
                                new_schedule = Schedule(
                                    doctor_id=doctor.doctor_id,
                                    date=current_date,
                                    time_slot=GENERAL_TIME_SLOT,
                                    department=doctor.department,
                                    room_address=GENERAL_ROOM_ADDRESS,  # 可根据科室进一步定制
                                    reg_fee=GENERAL_REG_FEE,
                                    total_slots=GENERAL_TOTAL_SLOTS,
                                    remain_slots=GENERAL_TOTAL_SLOTS
                                )
                                schedules_to_add.append(new_schedule)
                                general_schedules_created_count += 1
                            else:
                                general_schedules_skipped_count += 1
                        current_date += timedelta(days=1)
            print(
                f"--- 通用规则处理完毕。准备创建 {general_schedules_created_count} 条，跳过 {general_schedules_skipped_count} 条 ---")
            schedules_created_count += general_schedules_created_count
            schedules_skipped_count += general_schedules_skipped_count

        if schedules_to_add:
            try:
                db.session.add_all(schedules_to_add)
                db.session.commit()
                print(f"成功添加{len(schedules_to_add)}条新排班记录到数据库。")
                if schedules_skipped_count > 0:
                    print(f"因记录已存在而跳过了 {schedules_skipped_count} 条排班的创建。")
            except Exception as e:
                db.session.rollback()
                print(f"添加排班时发生数据库错误: {e}")
        else:
            print("没有新的排班记录需要添加。")
            if schedules_skipped_count > 0:
                print(f"因记录已存在而跳过了 {schedules_skipped_count} 条排班的创建。")

            if __name__ == '__main__':
                flask_app = create_app()  # 创建 Flask app 实例以获得应用上下文

            # 警告：执行此脚本可能会添加大量数据。
            # (可选) 清空旧的排班数据 - 极其谨慎操作！
            # confirm_delete = input("警告！是否要删除 'Schedule' 表中所有已存在的排班数据？这将不可恢复！(输入 'yes' 以确认): ")
            # if confirm_delete.lower() == 'yes':
            #     with flask_app.app_context():
            #         try:
            #             num_deleted = db.session.query(Schedule).delete()
            #             db.session.commit()
            #             print(f"已成功删除 {num_deleted} 条旧排班记录。")
            #         except Exception as e:
            #             db.session.rollback()
            #             print(f"删除旧排班记录时出错: {e}")
            # else:
            #     print("未删除旧排班记录。将尝试在现有数据基础上添加新排班。")

            print(f"准备为 {START_DATE.strftime('%Y-%m-%d')} 到 {END_DATE.strftime('%Y-%m-%d')} 期间的医生生成排班...")
            generate_schedules_for_period(flask_app)
            print("排班初始化脚本执行完毕。")
