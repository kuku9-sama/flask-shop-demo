from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
)


class LoginForm(FlaskForm):
    username = StringField(
        "用户名",
        validators=[DataRequired(message="请输入用户名"), Length(min=2, max=80)],
    )
    password = PasswordField("密码", validators=[DataRequired(message="请输入密码")])
    remember_me = BooleanField("记住我")
    submit = SubmitField("登录")


class RegisterForm(FlaskForm):
    username = StringField(
        "用户名",
        validators=[DataRequired(message="请输入用户名"), Length(min=2, max=80)],
    )
    email = StringField(
        "邮箱",
        validators=[
            DataRequired(message="请输入邮箱"),
            Email(message="请输入有效的邮箱地址"),
        ],
    )
    password = PasswordField(
        "密码",
        validators=[
            DataRequired(message="请输入密码"),
            Length(min=8, message="密码至少 8 位"),
        ],
    )
    password2 = PasswordField(
        "确认密码",
        validators=[
            DataRequired(message="请再次输入密码"),
            EqualTo("password", message="两次输入的密码不一致"),
        ],
    )
    submit = SubmitField("注册")


class ProductForm(FlaskForm):
    name = StringField(
        "商品名称",
        validators=[DataRequired(message="请输入商品名称"), Length(max=200)],
    )
    price = DecimalField(
        "价格",
        places=2,
        validators=[
            DataRequired(message="请输入价格"),
            NumberRange(min=0.01, message="价格必须大于 0"),
        ],
    )
    description = TextAreaField("商品描述", validators=[Optional()])
    image_url = StringField("图片 URL", validators=[Optional(), Length(max=500)])
    stock = IntegerField(
        "库存",
        validators=[
            DataRequired(message="请输入库存"),
            NumberRange(min=0, message="库存不能为负数"),
        ],
    )
    category = StringField("分类", validators=[Optional(), Length(max=100)])
    is_active = BooleanField("上架", default=True)
    submit = SubmitField("保存")


class CheckoutForm(FlaskForm):
    shipping_address = TextAreaField(
        "收货地址",
        validators=[
            DataRequired(message="请输入收货地址"),
            Length(max=500, message="地址不超过 500 个字符"),
        ],
    )
    submit = SubmitField("确认下单")
