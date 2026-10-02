from decimal import Decimal

from app.extensions import db
from app.models import CartItem, Order, OrderItem, Product


def login(client, username="alice", password="alice1234"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_index_lists_products(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "测试商品" in response.get_data(as_text=True)


def test_register_and_login(client):
    response = client.post(
        "/register",
        data={
            "username": "bob",
            "email": "bob@example.com",
            "password": "password123",
            "password2": "password123",
        },
        follow_redirects=True,
    )
    assert "注册成功" in response.get_data(as_text=True)

    client.get("/logout", follow_redirects=True)
    response = login(client, "bob", "password123")
    assert "欢迎回来" in response.get_data(as_text=True)


def test_login_ignores_external_next(client):
    response = client.post(
        "/login?next=https://evil.example/phish",
        data={"username": "alice", "password": "alice1234"},
    )
    assert response.status_code == 302
    assert "evil.example" not in response.headers["Location"]


def test_cart_requires_login(client):
    response = client.get("/cart")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_to_cart_stops_at_stock(app, client):
    login(client)
    for _ in range(7):
        client.post("/cart/add/1")

    with app.app_context():
        item = db.session.scalar(db.select(CartItem))
        assert item.quantity == 5


def test_checkout_creates_order_and_reduces_stock(app, client):
    login(client)
    client.post("/cart/add/1")

    response = client.post(
        "/checkout",
        data={"shipping_address": "广州市荔湾区测试路 1 号"},
        follow_redirects=True,
    )
    assert "下单成功" in response.get_data(as_text=True)

    with app.app_context():
        order = db.session.scalar(db.select(Order))
        assert order.total_amount == Decimal("19.90")
        assert db.session.scalar(db.select(CartItem)) is None
        assert db.session.get(Product, 1).stock == 4


def test_checkout_rejects_insufficient_stock(app, client):
    login(client)
    client.post("/cart/add/1")

    with app.app_context():
        product = db.session.get(Product, 1)
        product.stock = 0
        db.session.commit()

    response = client.post(
        "/checkout",
        data={"shipping_address": "广州市荔湾区测试路 1 号"},
        follow_redirects=True,
    )
    assert "库存不足" in response.get_data(as_text=True)

    with app.app_context():
        assert db.session.scalar(db.select(Order)) is None


def test_admin_pages_require_admin(client):
    login(client)
    response = client.get("/admin/", follow_redirects=True)
    assert "没有权限" in response.get_data(as_text=True)

    client.get("/logout", follow_redirects=True)
    login(client, "admin", "admin123")
    response = client.get("/admin/")
    assert response.status_code == 200


def test_admin_can_create_product(app, client):
    login(client, "admin", "admin123")
    response = client.post(
        "/admin/product/new",
        data={
            "name": "新品",
            "price": "12.50",
            "stock": "3",
            "category": "测试",
            "description": "",
            "image_url": "",
            "is_active": "y",
        },
        follow_redirects=True,
    )
    assert "已添加商品" in response.get_data(as_text=True)

    with app.app_context():
        product = db.session.scalar(db.select(Product).filter_by(name="新品"))
        assert product.price == Decimal("12.50")


def test_delete_product_keeps_order_history(app, client):
    login(client)
    client.post("/cart/add/1")
    client.post(
        "/checkout",
        data={"shipping_address": "广州市荔湾区测试路 1 号"},
    )
    client.get("/logout", follow_redirects=True)
    login(client, "admin", "admin123")

    client.post("/admin/product/1/delete", follow_redirects=True)

    with app.app_context():
        assert db.session.get(Product, 1) is None
        item = db.session.scalar(db.select(OrderItem))
        assert item.product_name == "测试商品"
        assert item.product_id is None
