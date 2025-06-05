import pyodbc

# --- 配置连接参数 ---
server_name = 'localhost'  # 对于 SQL Server 默认实例
#server_name = 'localhost\\SQLEXPRESS' # 对于名为 SQLEXPRESS 的实例 (请修改为你实际的实例名)
# server_name = '(localdb)\\MSSQLLocalDB' # 对于 SQL Server Express LocalDB

database_name = 'hospitalDB'
driver_name = 'ODBC Driver 17 for SQL Server' # 确保这个驱动已安装

# --- SQL Server Authentication 凭据 ---
sql_username = 'smgf'  # 替换为你创建的 SQL Server 登录名
sql_password = 'smgf' # 替换为对应的密码

# 构建连接字符串
conn_str = (
    f"DRIVER={{{driver_name}}};"
    f"SERVER={server_name};"
    f"DATABASE={database_name};"
    f"UID={sql_username};"  # User ID
    f"PWD={sql_password};"  # Password
    # "Trusted_Connection=yes;"  <-- 移除或注释掉这行
)

conn = None
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    print(f"Successfully connected to '{database_name}' on '{server_name}' using SQL Server Authentication (user: {sql_username})!")

    cursor.execute("SELECT @@VERSION;")
    row = cursor.fetchone()
    if row:
        print(f"SQL Server Version: {row[0]}")

except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"Error connecting to SQL Server with pyodbc: {sqlstate}")
    print(f"Error details: {ex}")
    if '28000' in sqlstate:
        print("Login failed. Check username, password, and ensure SQL Server Authentication is enabled on the server and for this login.")
    if '08001' in sqlstate:
        print("Server not found or not accessible. Check server name and that SQL Server service is running.")
    if 'IM002' in sqlstate:
        print(f"ODBC driver ('{driver_name}') not found. Check driver installation and name.")
finally:
    if conn:
        conn.close()
        print("Connection closed.")
