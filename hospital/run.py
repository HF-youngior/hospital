from app import create_app

app = create_app()
# # --- 添加以下代码来打印路由 ---
# if app:  # 确保 app 实例已成功创建
#     with app.app_context():  # 进入应用上下文，某些扩展或 url_map 可能需要
#         print("--- Registered Routes ---")
#         rules = []
#         for rule in app.url_map.iter_rules():
#             methods = ','.join(sorted(rule.methods))
#             rules.append((rule.endpoint, methods, str(rule)))
#
#         # 为了方便查看，可以按端点名称排序
#         sorted_rules = sorted(rules, key=lambda x: x[0])
#
#         for endpoint, methods, url_rule in sorted_rules:
#             print(f"Endpoint: {endpoint:<50} Methods: {methods:<25} URL: {url_rule}")
#         print("-------------------------")
# else:
#     print("Failed to create Flask app instance.")
# # --- 打印路由代码结束 ---
if __name__ == '__main__':
    app.run(debug=True) 