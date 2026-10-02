from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Product, User


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()

        admin = User(username="admin", email="admin@example.com", is_admin=True)
        admin.set_password("admin123")

        alice = User(username="alice", email="alice@example.com")
        alice.set_password("alice1234")

        product = Product(
            name="测试商品",
            price=Decimal("19.90"),
            stock=5,
            category="测试",
            description="用于测试的商品",
        )

        db.session.add_all([admin, alice, product])
        db.session.commit()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
