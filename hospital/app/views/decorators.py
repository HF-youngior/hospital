from functools import wraps
from flask import abort
from flask_login import current_user
# Python 装饰器 (Decorator)
# 它允许你限制只有拥有特定角色的已登录用户才能访问某些 Flask 路由（视图函数）。

def role_required(*roles):
    """
       这是一个装饰器工厂。它接收一个或多个角色名作为参数，
       然后返回一个实际的装饰器。
       *roles: 允许传入一个或多个角色名，例如 role_required('admin') 或 role_required('admin', 'doctor')
               这些角色名会被收集到一个名为 'roles' 的元组 (tuple) 中。
       """
    def decorator(f):
        """
               这才是真正的装饰器。它接收一个函数 f (即被装饰的 Flask 视图函数) 作为参数。
        """
        # 4. 使用 @wraps(f) 来保持被装饰函数的元信息
        # functools.wraps 是一个辅助装饰器，
        # 它会将被装饰函数 f 的一些重要属性(如 __name__, __doc__ 等) 复制到 decorated_function 上。
        # 这对于调试和内省非常有用，
        # 否则 decorated_function 的名字会是 'decorated_function'，而不是原始视图函数的名字。
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator 