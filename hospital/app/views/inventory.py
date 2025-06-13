
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Drug, CheckItem, db
from app.views.decorators import role_required
from wtforms import StringField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf import FlaskForm

inventory = Blueprint('inventory', __name__)

# 药品表单
class DrugForm(FlaskForm):
    name = StringField('药品名称', validators=[DataRequired(), Length(1, 100)])
    specification = StringField('规格', validators=[DataRequired(), Length(1, 100)])
    price = FloatField('价格', validators=[DataRequired(), NumberRange(min=0)])
    usage = StringField('用法', validators=[DataRequired(), Length(1, 50)])
    frequency = StringField('使用频率', validators=[DataRequired(), Length(1, 50)])
    stock = IntegerField('库存', validators=[DataRequired(), NumberRange(min=0)])
    remark = StringField('备注', validators=[Length(0, 200)])
    status = StringField('状态', validators=[DataRequired(), Length(1, 20)])
    insurance_rate = FloatField('医保报销比例', validators=[DataRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('提交')

# 检查项目表单
class CheckItemForm(FlaskForm):
    name = StringField('检查项目名称', validators=[DataRequired(), Length(1, 100)])
    price = FloatField('价格', validators=[DataRequired(), NumberRange(min=0)])
    department = StringField('科室', validators=[DataRequired(), Length(1, 50)])
    insurance_rate = FloatField('医保报销比例', validators=[DataRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('提交')

# 搜索表单
class SearchForm(FlaskForm):
    search_type = SelectField('搜索类型', choices=[('name', '名称'), ('id', 'ID')], validators=[DataRequired()])
    query = StringField('搜索内容', validators=[DataRequired()])
    submit = SubmitField('搜索')

# 药品库列表
@inventory.route('/drug/list', methods=['GET', 'POST'])
@login_required
def drug_list():
    form = SearchForm()
    drugs = Drug.query.all()

    if form.validate_on_submit():
        search_type = form.search_type.data
        query = form.query.data
        if search_type == 'name':
            drugs = Drug.query.filter(Drug.name.ilike(f'%{query}%')).all()
        else:  # search by ID
            try:
                drugs = Drug.query.filter_by(drug_id=int(query)).all()
            except ValueError:
                flash('请输入有效的药品ID', 'danger')
                drugs = []

    return render_template('drug_list.html', drugs=drugs, form=form)

# 编辑药品（仅管理员）
@inventory.route('/drug/edit/<int:drug_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_drug(drug_id):
    drug = Drug.query.get_or_404(drug_id)
    form = DrugForm(obj=drug)

    if form.validate_on_submit():
        form.populate_obj(drug)
        try:
            db.session.commit()
            flash('药品信息更新成功！', 'success')
            return redirect(url_for('inventory.drug_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')

    return render_template('drug_edit.html', form=form, drug=drug)

# 检查项目库列表
@inventory.route('/check_item/list', methods=['GET', 'POST'])
@login_required
def check_item_list():
    form = SearchForm()
    check_items = CheckItem.query.all()

    if form.validate_on_submit():
        search_type = form.search_type.data
        query = form.query.data
        if search_type == 'name':
            check_items = CheckItem.query.filter(CheckItem.name.ilike(f'%{query}%')).all()
        else:  # search by ID
            try:
                check_items = CheckItem.query.filter_by(item_id=int(query)).all()
            except ValueError:
                flash('请输入有效的检查项目ID', 'danger')
                check_items = []

    return render_template('check_item_list.html', check_items=check_items, form=form)

# 编辑检查项目（仅管理员）
@inventory.route('/check_item/edit/<int:item_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_check_item(item_id):
    check_item = CheckItem.query.get_or_404(item_id)
    form = CheckItemForm(obj=check_item)

    if form.validate_on_submit():
        form.populate_obj(check_item)
        try:
            db.session.commit()
            flash('检查项目信息更新成功！', 'success')
            return redirect(url_for('inventory.check_item_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败：{str(e)}', 'danger')

    return render_template('check_item_edit.html', form=form, check_item=check_item)
# 新增药品（仅管理员）
@inventory.route('/drug/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_drug():
    form = DrugForm()
    if form.validate_on_submit():
        drug = Drug(
            name=form.name.data,
            specification=form.specification.data,
            price=form.price.data,
            usage=form.usage.data,
            frequency=form.frequency.data,
            stock=form.stock.data,
            remark=form.remark.data,
            status=form.status.data,
            insurance_rate=form.insurance_rate.data
        )
        try:
            db.session.add(drug)
            db.session.commit()
            flash('药品添加成功！', 'success')
            return redirect(url_for('inventory.drug_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败：{str(e)}', 'danger')
    return render_template('drug_add.html', form=form)

# 新增检查项目（仅管理员）
@inventory.route('/check_item/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_check_item():
    form = CheckItemForm()
    if form.validate_on_submit():
        check_item = CheckItem(
            name=form.name.data,
            price=form.price.data,
            department=form.department.data,
            insurance_rate=form.insurance_rate.data
        )
        try:
            db.session.add(check_item)
            db.session.commit()
            flash('检查项目添加成功！', 'success')
            return redirect(url_for('inventory.check_item_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失败：{str(e)}', 'danger')
    return render_template('check_item_add.html', form=form)