from decimal import Decimal

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from .extensions import db
from .forms import CheckoutForm
from .models import CartItem, Order, OrderItem, Product

bp = Blueprint("shop", __name__)

ZERO = Decimal("0.00")


def cart_total(items):
    return sum((item.product.price * item.quantity for item in items), ZERO)


def parse_quantity(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


@bp.route("/")
def index():
    category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip()

    stmt = db.select(Product).where(Product.is_active.is_(True))
    if category:
        stmt = stmt.where(Product.category == category)
    if search:
        stmt = stmt.where(Product.name.contains(search))
    products = db.session.scalars(stmt.order_by(Product.created_at.desc())).all()

    categories = db.session.scalars(
        db.select(Product.category)
        .where(Product.is_active.is_(True), Product.category != "")
        .distinct()
        .order_by(Product.category)
    ).all()

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        current_category=category,
        search=search,
    )


@bp.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if product is None or not product.is_active:
        flash("商品不存在或已下架", "danger")
        return redirect(url_for("shop.index"))
    return render_template("product.html", product=product)


@bp.route("/cart")
@login_required
def cart():
    items = db.session.scalars(
        db.select(CartItem)
        .where(CartItem.user_id == current_user.id)
        .order_by(CartItem.id)
    ).all()
    return render_template("cart.html", cart_items=items, total=cart_total(items))


@bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if product is None or not product.is_active:
        flash("商品不存在或已下架", "danger")
        return redirect(url_for("shop.index"))
    if product.stock <= 0:
        flash(f"「{product.name}」暂时缺货", "warning")
        return redirect(url_for("shop.product_detail", product_id=product.id))

    item = db.session.scalar(
        db.select(CartItem).filter_by(
            user_id=current_user.id, product_id=product.id
        )
    )
    if item is None:
        db.session.add(
            CartItem(user_id=current_user.id, product_id=product.id, quantity=1)
        )
    elif item.quantity >= product.stock:
        flash(f"库存只剩 {product.stock} 件", "warning")
        return redirect(url_for("shop.product_detail", product_id=product.id))
    else:
        item.quantity += 1

    db.session.commit()
    flash(f"已加入购物车：{product.name}", "success")
    return redirect(url_for("shop.product_detail", product_id=product.id))


@bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart(item_id):
    item = db.session.get(CartItem, item_id)
    if item is None or item.user_id != current_user.id:
        flash("购物车中没有这件商品", "danger")
        return redirect(url_for("shop.cart"))

    quantity = parse_quantity(request.form.get("quantity"))
    if quantity is None:
        flash("数量格式不正确", "danger")
    elif quantity <= 0:
        db.session.delete(item)
        db.session.commit()
        flash("已从购物车移除", "info")
    elif quantity > item.product.stock:
        flash(f"库存只剩 {item.product.stock} 件", "warning")
    else:
        item.quantity = quantity
        db.session.commit()
        flash("数量已更新", "success")

    return redirect(url_for("shop.cart"))


@bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    item = db.session.get(CartItem, item_id)
    if item is None or item.user_id != current_user.id:
        flash("购物车中没有这件商品", "danger")
        return redirect(url_for("shop.cart"))

    db.session.delete(item)
    db.session.commit()
    flash("已从购物车移除", "info")
    return redirect(url_for("shop.cart"))


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = db.session.scalars(
        db.select(CartItem)
        .where(CartItem.user_id == current_user.id)
        .order_by(CartItem.id)
    ).all()
    if not items:
        flash("购物车是空的", "warning")
        return redirect(url_for("shop.cart"))

    form = CheckoutForm()
    if form.validate_on_submit():
        out_of_stock = [
            item.product.name
            for item in items
            if item.product.stock < item.quantity
        ]
        if out_of_stock:
            flash("库存不足：" + "、".join(out_of_stock), "danger")
            return redirect(url_for("shop.cart"))

        order = Order(
            user_id=current_user.id,
            total_amount=cart_total(items),
            shipping_address=form.shipping_address.data,
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=item.product.name,
                    price=item.product.price,
                    quantity=item.quantity,
                )
            )
            item.product.stock -= item.quantity
            db.session.delete(item)

        db.session.commit()
        flash("订单已提交", "success")
        return redirect(url_for("shop.order_detail", order_id=order.id))

    return render_template(
        "checkout.html", form=form, cart_items=items, total=cart_total(items)
    )


@bp.route("/orders")
@login_required
def my_orders():
    orders = db.session.scalars(
        db.select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).all()
    return render_template("orders.html", orders=orders)


@bp.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if order is None or order.user_id != current_user.id:
        flash("订单不存在", "danger")
        return redirect(url_for("shop.my_orders"))
    return render_template("order_success.html", order=order)
