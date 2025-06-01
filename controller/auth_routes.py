from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database.db import db
from model.models import Usuarios
from controller.forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__,
                    template_folder='../view/templates/auth',
                    static_folder='../view/static', # if you have auth-specific static files
                    url_prefix='/auth') # Optional: prefix all routes in this blueprint with /auth

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Usuarios(username=form.username.data,
                    email=form.email.data,
                    role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', title='Register', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuarios.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user) # 'remember=form.remember_me.data' can be added if you have a remember_me field
            flash('Login successful!', 'success')
            # next_page = request.args.get('next')
            # return redirect(next_page) if next_page else redirect(url_for('main.home'))
            return redirect(url_for('main.home')) # Or a dashboard page
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
