import os
from decimal import Decimal

from flask import current_app

from .extensions import db
from .models import Product, User

SAMPLE_PRODUCTS = [
    {
        "name": "无线蓝牙耳机",
        "price": Decimal("299.00"),
        "description": "主动降噪，续航 30 小时，蓝牙 5.3 连接稳定。入耳式设计，适合长时间佩戴。",
        "image_url": "/static/images/product-1.svg",
        "stock": 50,
        "category": "数码电子",
    },
    {
        "name": "机械键盘",
        "price": Decimal("459.00"),
        "description": "87 键紧凑布局，Cherry MX 红轴，RGB 背光，PBT 键帽，全键无冲。",
        "image_url": "/static/images/product-2.svg",
        "stock": 30,
        "category": "数码电子",
    },
    {
        "name": "纯棉 T 恤",
        "price": Decimal("89.00"),
        "description": "100% 精梳棉，柔软透气，不易变形。简约纯色，多色多码可选。",
        "image_url": "/static/images/product-3.svg",
        "stock": 200,
        "category": "服装",
    },
    {
        "name": "不锈钢保温杯",
        "price": Decimal("128.00"),
        "description": "316 不锈钢内胆，12 小时保温保冷，500ml 容量，一键开盖。",
        "image_url": "/static/images/product-4.svg",
        "stock": 100,
        "category": "生活用品",
    },
    {
        "name": "Python 编程从入门到实践",
        "price": Decimal("69.80"),
        "description": "覆盖 Python 基础语法、数据结构、Web 开发和数据可视化，适合零基础学习。",
        "image_url": "/static/images/product-5.svg",
        "stock": 80,
        "category": "图书",
    },
    {
        "name": "运动跑步鞋",
        "price": Decimal("399.00"),
        "description": "单只 230g，高弹 EVA 中底，透气网面，防滑橡胶大底。",
        "image_url": "/static/images/product-6.svg",
        "stock": 60,
        "category": "运动户外",
    },
    {
        "name": "智能台灯",
        "price": Decimal("199.00"),
        "description": "LED 护眼，无频闪无蓝光危害，色温亮度无极调节，带 USB 充电口。",
        "image_url": "/static/images/product-7.svg",
        "stock": 45,
        "category": "生活用品",
    },
    {
        "name": "双肩背包",
        "price": Decimal("259.00"),
        "description": "可放 15.6 寸笔记本，防泼水面料，人体工学背负，多隔层收纳。",
        "image_url": "/static/images/product-8.svg",
        "stock": 70,
        "category": "箱包",
    },
]


def seed_if_empty():
    changed = False

    if db.session.scalar(db.select(Product.id).limit(1)) is None:
        db.session.add_all(Product(**item) for item in SAMPLE_PRODUCTS)
        changed = True

    if db.session.scalar(db.select(User).filter_by(username="admin")) is None:
        admin = User(
            username="admin",
            email="admin@example.com",
            is_admin=True,
        )
        admin.set_password(os.environ.get("ADMIN_PASSWORD", "admin123"))
        db.session.add(admin)
        changed = True

    if changed:
        db.session.commit()
        current_app.logger.info("已写入示例数据")
