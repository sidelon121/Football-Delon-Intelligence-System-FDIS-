from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)
oauth = OAuth()

# Initialize OAuth
def init_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    oauth.register(
        name='github',
        client_id=app.config.get('GITHUB_CLIENT_ID'),
        client_secret=app.config.get('GITHUB_CLIENT_SECRET'),
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'}
    )

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('main.index'))
        else:
            flash('Login failed. Please check your email and password.', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))
            
        new_user = User(email=email, name=name)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# --- OAuth Routes ---

@auth_bp.route('/login/google')
def login_google():
    redirect_uri=url_for("google.authorized", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/authorize/google')
def authorize_google():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash('Failed to get user info from Google.', 'error')
        return redirect(url_for('auth.login'))
        
    email = user_info['email']
    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(
            email=email,
            name=user_info.get('name'),
            google_id=user_info.get('sub'),
            avatar_url=user_info.get('picture')
        )
        db.session.add(user)
        db.session.commit()
    elif not user.google_id:
        user.google_id = user_info.get('sub')
        user.avatar_url = user_info.get('picture')
        db.session.commit()
        
    login_user(user)
    return redirect(url_for('main.index'))

@auth_bp.route('/login/github')
def login_github():
    redirect_uri=url_for("google.authorized", _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@auth_bp.route('/authorize/github')
def authorize_github():
    token = oauth.github.authorize_access_token()
    resp = oauth.github.get('user')
    user_info = resp.json()
    
    # Github email is often hidden, need separate call
    resp_email = oauth.github.get('user/emails')
    emails = resp_email.json()
    primary_email = next((e['email'] for e in emails if e['primary']), emails[0]['email'] if emails else None)
    
    if not primary_email:
        flash('Failed to get email from GitHub.', 'error')
        return redirect(url_for('auth.login'))
        
    user = User.query.filter_by(email=primary_email).first()
    
    if not user:
        user = User(
            email=primary_email,
            name=user_info.get('name') or user_info.get('login'),
            github_id=str(user_info.get('id')),
            avatar_url=user_info.get('avatar_url')
        )
        db.session.add(user)
        db.session.commit()
    elif not user.github_id:
        user.github_id = str(user_info.get('id'))
        user.avatar_url = user_info.get('avatar_url')
        db.session.commit()
        
    login_user(user)
    return redirect(url_for('main.index'))
