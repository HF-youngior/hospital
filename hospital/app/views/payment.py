from flask import Flask, render_template, request, redirect, url_for, abort, Blueprint
import uuid  # 用于生成唯一的订单号

payment = Blueprint('payment', __name__, url_prefix='/payment')

# 支付类型与中文描述映射
PAYMENT_TYPE_MAP = {
    "registration": "门诊挂号",
    "examination": "项目检查",
    "medicine": "药品购买"
}

# 支付成功后跳转的页面映射
SUCCESS_REDIRECT_MAP = {
    "registration": "registration_success.html",
    "examination": "examination_success.html",
    "medicine": "medicine_success.html"
}


@payment.route('/')
def index():
    # 这是一个简单的首页，提供发起支付的入口
    # 在您的实际应用中，这些链接会在挂号、开检查单、开药方等流程后生成
    return """
    <h1>医院业务系统 - 支付模拟</h1>
    <p>选择一项业务以发起支付：</p>
    <ul>
        <li><a href="{}">模拟挂号支付 (15元)</a></li>
        <li><a href="{}">模拟检查项目支付 (150元)</a></li>
        <li><a href="{}">模拟药品支付 (88元)</a></li>
    </ul>
    """.format(
        url_for('initiate_payment', type='registration', amount=15),
        url_for('initiate_payment', type='examination', amount=150),
        url_for('initiate_payment', type='medicine', amount=88)
    )


@payment.route('/initiate_payment')
def initiate_payment():
    """
    发起支付请求。
    在实际应用中，此路由可能在用户完成挂号选择、医生开具检查单/处方后被调用。
    参数:
        type: 支付类型 (registration, examination, medicine)
        amount: 支付金额
        order_id: (可选) 如果已有订单ID，则传入；否则自动生成
    """
    payment_type = request.args.get('type')
    amount = request.args.get('amount', type=float)  # 确保是数字
    order_id = request.args.get('order_id')

    if not payment_type or payment_type not in PAYMENT_TYPE_MAP:
        abort(400, "无效的支付类型")
    if amount is None or amount <= 0:
        abort(400, "无效的支付金额")

    # 如果没有传入order_id，则生成一个新的
    if not order_id:
        order_id = f"{payment_type.upper()[:3]}-{str(uuid.uuid4())[:8].upper()}"

    # 存储（或更新）订单信息（模拟）
    mock_orders[order_id] = {
        "type": payment_type,
        "amount": amount,
        "status": "pending"  # 初始状态为待支付
    }

    payment_reason_text = PAYMENT_TYPE_MAP.get(payment_type, "未知项目")

    return render_template('QRcode.html',
                           payment_type=payment_type,
                           payment_reason_text=payment_reason_text,
                           amount=amount,
                           order_id=order_id)


@payment.route('/process_payment')
def process_payment():
    """
    处理支付结果 (模拟)。
    在真实系统中，这通常是一个回调URL，由支付网关在用户支付成功后异步调用。
    这里我们通过用户点击按钮来模拟。
    参数:
        status: 'success' 或 'cancelled'
        type: 支付类型
        order_id: 订单ID
        amount: (可选) 支付金额，用于取消时重新支付
    """
    status = request.args.get('status')
    payment_type = request.args.get('type')
    order_id = request.args.get('order_id')
    amount_str = request.args.get('amount')  # 用于取消时重新支付

    if not all([status, payment_type, order_id]):
        abort(400, "缺少必要的支付结果参数")

    if order_id not in mock_orders:
        abort(404, "订单不存在或已过期")

    order_details = mock_orders[order_id]
    if order_details["type"] != payment_type:
        abort(400, "订单类型不匹配")

    if status == 'success':
        # 模拟：更新订单状态为已支付
        mock_orders[order_id]['status'] = 'paid'
        # 实际应用中：
        # 1. 验证支付签名 (如果这是支付网关回调)
        # 2. 再次确认订单金额与实际支付金额是否一致
        # 3. 更新数据库中的订单状态
        # 4. 可能触发后续业务逻辑 (如通知药房、更新挂号队列等)

        success_template = SUCCESS_REDIRECT_MAP.get(payment_type)
        if not success_template:
            abort(500, "未找到对应的成功页面模板")

        print(f"订单 {order_id} ({PAYMENT_TYPE_MAP[payment_type]}) 支付成功，金额: {order_details['amount']}")
        return render_template(success_template, order_id=order_id)

    elif status == 'cancelled':
        mock_orders[order_id]['status'] = 'cancelled'
        print(f"订单 {order_id} ({PAYMENT_TYPE_MAP[payment_type]}) 支付已取消")
        # 传递原始金额，以便“重新支付”链接能正确工作
        amount_to_repay = order_details.get('amount', 0) if amount_str is None else amount_str

        return render_template('payment_cancelled.html',
                               order_id=order_id,
                               payment_type=payment_type,
                               amount_to_repay=amount_to_repay)
    else:
        abort(400, "无效的支付状态")


# 为成功页面和取消页面提供返回首页的链接
@payment.route('/registration_success')
def registration_success():
    order_id = request.args.get('order_id', '未知订单')
    return render_template('registration_success.html', order_id=order_id)


@payment.route('/examination_success')
def examination_success():
    order_id = request.args.get('order_id', '未知订单')
    return render_template('examination_success.html', order_id=order_id)


@payment.route('/medicine_success')
def medicine_success():
    order_id = request.args.get('order_id', '未知订单')
    return render_template('medicine_success.html', order_id=order_id)


