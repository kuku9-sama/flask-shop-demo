from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .extensions import db
from .forms import ProductForm
from .models import ORDER_STATUSES, Order, Product

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login", next=request.path))
        if not current_user.is_admin:
            flash("没有权限访问管理后台", "danger")
            return redirect(url_for("shop.index"))
        return view(*args, **kwargs)

    return wrapped


@bp.route("/")
@admin_required
def products():
    items = db.session.scalars(
        db.select(Product).order_by(Product.created_at.desc())
    ).all()
    return render_template("admin/products.html", products=items)


@bp.route("/product/new", methods=["GET", "POST"])
@admin_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data or "",
            image_url=form.image_url.data or "",
            stock=form.stock.data,
            category=form.category.data or "",
            is_active=form.is_active.data,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"已添加商品：{product.name}", "success")
        return redirect(url_for("admin.products"))
    return render_template("admin/product_form.html", form=form, title="添加商品")


@bp.route("/product/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        flash("商品不存在", "danger")
        return redirect(url_for("admin.products"))

    form = ProductForm(obj=product)
    if form.validate_on_submit():
        product.name = form.name.data
        product.price = form.price.data
        product.description = form.description.data or ""
        product.image_url = form.image_url.data or ""
        product.stock = form.stock.data
        product.category = form.category.data or ""
        product.is_active = form.is_active.data
        db.session.commit()
        flash(f"已更新商品：{product.name}", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", form=form, title="编辑商品")


@bp.route("/product/<int:product_id>/delete", methods=["POST"])
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        flash("商品不存在", "danger")
        return redirect(url_for("admin.products"))

    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f"已删除商品：{name}", "success")
    return redirect(url_for("admin.products"))


@bp.route("/orders")
@admin_required
def orders():
    items = db.session.scalars(
        db.select(Order).order_by(Order.created_at.desc())
    ).all()
    return render_template("admin/orders.html", orders=items)


@bp.route("/order/<int:order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if order is None:
        flash("订单不存在", "danger")
        return redirect(url_for("admin.orders"))

    status = request.form.get("status", "")
    if status not in ORDER_STATUSES:
        flash("无效的订单状态", "danger")
        return redirect(url_for("admin.orders"))

    order.status = status
    db.session.commit()
    flash(f"订单 #{order.id} 状态已更新", "success")
    return redirect(url_for("admin.orders"))
