from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from database import db
from models import User

users_view_bp = Blueprint("users_view", __name__)

ROLES = ["admin", "editor", "viewer"]


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@users_view_bp.before_request
@login_required
def require_login():
    pass


@users_view_bp.route("/users")
@admin_required
def list_users():
    users = User.query.order_by(User.role, User.name).all()
    return render_template("users/list.html", users=users, active_page="users")


@users_view_bp.route("/users/new", methods=["GET", "POST"])
@admin_required
def new_user():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "viewer")

        if not email or not name or not password:
            flash("Email, name, and password are required.", "danger")
            return render_template("users/form.html", user=None, roles=ROLES, active_page="users")

        if User.query.filter_by(email=email).first():
            flash(f"A user with email '{email}' already exists.", "danger")
            return render_template("users/form.html", user=None, roles=ROLES, active_page="users")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("users/form.html", user=None, roles=ROLES, active_page="users")

        user = User(email=email, name=name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f"User '{name}' created successfully.", "success")
        return redirect(url_for("users_view.list_users"))

    return render_template("users/form.html", user=None, roles=ROLES, active_page="users")


@users_view_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        role = request.form.get("role", user.role)
        is_active = request.form.get("is_active") == "1"
        new_password = request.form.get("password", "").strip()

        if not name:
            flash("Name is required.", "danger")
            return render_template("users/form.html", user=user, roles=ROLES, active_page="users")

        # Prevent removing the last admin
        if user.role == "admin" and role != "admin":
            admin_count = User.query.filter_by(role="admin", is_active=True).count()
            if admin_count <= 1:
                flash("Cannot demote the only admin account.", "danger")
                return render_template("users/form.html", user=user, roles=ROLES, active_page="users")

        user.name = name
        user.role = role
        user.is_active = is_active

        if new_password:
            if len(new_password) < 8:
                flash("Password must be at least 8 characters.", "danger")
                return render_template("users/form.html", user=user, roles=ROLES, active_page="users")
            user.set_password(new_password)

        db.session.commit()
        flash(f"User '{user.name}' updated.", "success")
        return redirect(url_for("users_view.list_users"))

    return render_template("users/form.html", user=user, roles=ROLES, active_page="users")


@users_view_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("users_view.list_users"))

    if user.role == "admin":
        admin_count = User.query.filter_by(role="admin", is_active=True).count()
        if admin_count <= 1:
            flash("Cannot delete the only admin account.", "danger")
            return redirect(url_for("users_view.list_users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User '{user.name}' deleted.", "success")
    return redirect(url_for("users_view.list_users"))
