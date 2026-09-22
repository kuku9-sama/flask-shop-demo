from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .forms import LoginForm, RegisterForm
from .models import User

bp = Blueprint("auth", __name__)


def safe_next_url(target):
    # 只接受站内路径，挡掉 //evil.com 和绝对地址
    if not target:
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/"):
        return None
    return target


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        exists = db.session.scalar(
            db.select(User).filter(
                (User.username == form.username.data) | (User.email == form.email.data)
            )
        )
        if exists:
            flash("用户名或邮箱已被注册", "danger")
            return render_template("register.html", form=form)

        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("注册成功，欢迎！", "success")
        return redirect(url_for("shop.index"))

    return render_template("register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("shop.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            db.select(User).filter_by(username=form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash("用户名或密码错误", "danger")
            return render_template("login.html", form=form)

        login_user(user, remember=form.remember_me.data)
        flash(f"欢迎回来，{user.username}", "success")
        return redirect(
            safe_next_url(request.args.get("next")) or url_for("shop.index")
        )

    return render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已退出登录", "info")
    return redirect(url_for("shop.index"))
